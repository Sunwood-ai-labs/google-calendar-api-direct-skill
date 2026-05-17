#!/usr/bin/env python3
"""Small Google Calendar API CLI for local Codex use."""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_DIR = Path.home() / ".codex" / "google-calendar-api-direct"
CLIENT_SECRET_PATH = Path(os.environ.get("GCAL_CLIENT_SECRET", CONFIG_DIR / "client_secret.json"))
TOKEN_PATH = Path(os.environ.get("GCAL_TOKEN_FILE", CONFIG_DIR / "token.json"))
DEFAULT_SCOPE = os.environ.get(
    "GCAL_SCOPES",
    "https://www.googleapis.com/auth/calendar.app.created",
)
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/calendar/v3"


class ApiError(RuntimeError):
    pass


def eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def client_config() -> dict:
    if not CLIENT_SECRET_PATH.exists():
        raise ApiError(
            f"Missing OAuth client JSON: {CLIENT_SECRET_PATH}\n"
            "Create a Google Cloud OAuth Desktop client, download JSON, and place it there."
        )
    raw = load_json(CLIENT_SECRET_PATH)
    cfg = raw.get("installed") or raw.get("web") or raw
    if not cfg.get("client_id"):
        raise ApiError("OAuth client JSON does not contain client_id.")
    return cfg


def parse_scopes(scope_text: str | None) -> list[str]:
    scope_text = scope_text or DEFAULT_SCOPE
    return [s.strip() for s in scope_text.replace(",", " ").split() if s.strip()]


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_pkce() -> tuple[str, str]:
    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    code: str | None = None
    error: str | None = None
    expected_state: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        state = params.get("state", [""])[0]
        if self.expected_state and state != self.expected_state:
            type(self).error = "state_mismatch"
        elif "error" in params:
            type(self).error = params["error"][0]
        else:
            type(self).code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Google Calendar API Direct</h1>"
            b"<p>Authorization received. You can close this tab.</p></body></html>"
        )

    def log_message(self, fmt: str, *args: object) -> None:
        return


def post_form(url: str, data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    return request_json(req)


def request_json(req: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = body
        raise ApiError(f"HTTP {exc.code}: {detail}") from exc


def auth(args: argparse.Namespace) -> None:
    cfg = client_config()
    scopes = parse_scopes(args.scopes)
    verifier, challenge = make_pkce()
    state = secrets.token_urlsafe(24)
    server = http.server.HTTPServer(("127.0.0.1", 0), OAuthHandler)
    OAuthHandler.code = None
    OAuthHandler.error = None
    OAuthHandler.expected_state = state
    redirect_uri = f"http://127.0.0.1:{server.server_port}/"
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print(f"Open this URL if the browser does not open:\n{url}", file=sys.stderr)
    webbrowser.open(url)
    deadline = time.time() + 300
    while time.time() < deadline and not OAuthHandler.code and not OAuthHandler.error:
        server.handle_request()
    if OAuthHandler.error:
        raise ApiError(f"OAuth failed: {OAuthHandler.error}")
    if not OAuthHandler.code:
        raise ApiError("Timed out waiting for OAuth callback.")
    token = post_form(
        TOKEN_URL,
        {
            "client_id": cfg["client_id"],
            "client_secret": cfg.get("client_secret", ""),
            "code": OAuthHandler.code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    token["scope_requested"] = scopes
    save_json(TOKEN_PATH, token)
    print(json.dumps({"token_file": str(TOKEN_PATH), "scopes": scopes}, ensure_ascii=False, indent=2))


def refresh_token(token: dict) -> dict:
    cfg = client_config()
    refresh = token.get("refresh_token")
    if not refresh:
        raise ApiError("Token has no refresh_token. Run auth again.")
    new_token = post_form(
        TOKEN_URL,
        {
            "client_id": cfg["client_id"],
            "client_secret": cfg.get("client_secret", ""),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
    )
    token.update(new_token)
    token["refresh_token"] = refresh
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    save_json(TOKEN_PATH, token)
    return token


def access_token() -> str:
    if not TOKEN_PATH.exists():
        raise ApiError(f"Missing token: {TOKEN_PATH}. Run auth first.")
    token = load_json(TOKEN_PATH)
    if int(token.get("expires_at", 0)) <= int(time.time()):
        token = refresh_token(token)
    return token["access_token"]


def api(method: str, path: str, body: dict | None = None, query: dict | None = None) -> dict:
    url = API_BASE + path
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {access_token()}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    return request_json(req)


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def calendars_list(args: argparse.Namespace) -> None:
    print_json(api("GET", "/users/me/calendarList", query={"maxResults": args.max_results}))


def calendars_create(args: argparse.Namespace) -> None:
    body = {
        "summary": args.summary,
        "description": args.description,
        "timeZone": args.time_zone,
    }
    print_json(api("POST", "/calendars", body={k: v for k, v in body.items() if v is not None}))


def calendars_color(args: argparse.Namespace) -> None:
    body = {"backgroundColor": args.background, "foregroundColor": args.foreground}
    cid = urllib.parse.quote(args.calendar_id, safe="")
    print_json(api("PATCH", f"/users/me/calendarList/{cid}", body=body, query={"colorRgbFormat": "true"}))


def colors_get(args: argparse.Namespace) -> None:
    print_json(api("GET", "/colors"))


def events_create(args: argparse.Namespace) -> None:
    body = {
        "summary": args.summary,
        "description": args.description,
        "location": args.location,
        "colorId": args.color_id,
        "start": {"dateTime": args.start, "timeZone": args.time_zone},
        "end": {"dateTime": args.end, "timeZone": args.time_zone},
    }
    if args.url:
        desc = body.get("description") or ""
        body["description"] = (desc + "\n\nURL: " + args.url).strip()
    if args.reminder_minutes is not None:
        body["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": args.reminder_minutes}],
        }
    cid = urllib.parse.quote(args.calendar_id, safe="")
    print_json(api("POST", f"/calendars/{cid}/events", body={k: v for k, v in body.items() if v is not None}))


def events_search(args: argparse.Namespace) -> None:
    cid = urllib.parse.quote(args.calendar_id, safe="")
    query = {
        "q": args.query,
        "timeMin": args.time_min,
        "timeMax": args.time_max,
        "maxResults": args.max_results,
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    print_json(api("GET", f"/calendars/{cid}/events", query=query))


def events_get(args: argparse.Namespace) -> None:
    cid = urllib.parse.quote(args.calendar_id, safe="")
    eid = urllib.parse.quote(args.event_id, safe="")
    print_json(api("GET", f"/calendars/{cid}/events/{eid}"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Google Calendar API Direct CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("auth", help="Run local OAuth flow")
    p.add_argument("--scopes", help="Space or comma separated OAuth scopes")
    p.set_defaults(func=auth)

    cal = sub.add_parser("calendars", help="Calendar operations").add_subparsers(dest="calendar_command", required=True)
    p = cal.add_parser("list")
    p.add_argument("--max-results", type=int, default=50)
    p.set_defaults(func=calendars_list)
    p = cal.add_parser("create")
    p.add_argument("--summary", required=True)
    p.add_argument("--description")
    p.add_argument("--time-zone", default="Asia/Tokyo")
    p.set_defaults(func=calendars_create)
    p = cal.add_parser("color")
    p.add_argument("--calendar-id", required=True)
    p.add_argument("--background", required=True)
    p.add_argument("--foreground", default="#ffffff")
    p.set_defaults(func=calendars_color)

    p = sub.add_parser("colors", help="Get Calendar API color palettes")
    p.set_defaults(func=colors_get)

    ev = sub.add_parser("events", help="Event operations").add_subparsers(dest="event_command", required=True)
    p = ev.add_parser("create")
    p.add_argument("--calendar-id", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--time-zone", default="Asia/Tokyo")
    p.add_argument("--description")
    p.add_argument("--location")
    p.add_argument("--url")
    p.add_argument("--color-id")
    p.add_argument("--reminder-minutes", type=int)
    p.set_defaults(func=events_create)
    p = ev.add_parser("search")
    p.add_argument("--calendar-id", required=True)
    p.add_argument("--time-min", required=True)
    p.add_argument("--time-max", required=True)
    p.add_argument("--query")
    p.add_argument("--max-results", type=int, default=20)
    p.set_defaults(func=events_search)
    p = ev.add_parser("get")
    p.add_argument("--calendar-id", required=True)
    p.add_argument("--event-id", required=True)
    p.set_defaults(func=events_get)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except ApiError as exc:
        eprint(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
