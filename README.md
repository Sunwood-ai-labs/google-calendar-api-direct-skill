# Google Calendar API Direct Skill

[日本語](README.ja.md)

A Codex skill and small standard-library Python CLI for using the Google Calendar API directly when the built-in Google Calendar connector is not enough.

This is meant for local, user-authorized automation such as:

- creating secondary calendars
- setting calendar display colors
- creating sample events with locations, descriptions, URLs, reminders, and event color IDs
- reading back created calendars and events to verify API writes

## Why This Exists

The built-in Google Calendar connector is convenient for ordinary scheduling work. Direct API access is useful when a workflow needs calendar-level operations, reproducible local smoke tests, or explicit API evidence.

## Repository Layout

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/calendar-api.md
└── scripts/gcal_api.py
```

## Requirements

- Python 3.10 or newer
- A Google Cloud project with Google Calendar API enabled
- An OAuth client of type **Desktop app**

The CLI intentionally uses only Python's standard library. No package install is required.

## Credential Safety

Do not commit OAuth credentials or tokens.

The CLI stores local credentials outside the repository by default:

```text
~/.codex/google-calendar-api-direct/client_secret.json
~/.codex/google-calendar-api-direct/token.json
```

You can override those paths for tests or alternate profiles:

```bash
export GCAL_CLIENT_SECRET=/path/to/client_secret.json
export GCAL_TOKEN_FILE=/path/to/token.json
```

## Setup

1. Create or select a Google Cloud project.
2. Enable **Google Calendar API**.
3. Configure Google Auth Platform / OAuth consent.
4. Create an OAuth client of type **Desktop app**.
5. Download the OAuth client JSON.
6. Save it locally:

```bash
mkdir -p ~/.codex/google-calendar-api-direct
cp ~/Downloads/client_secret_*.json ~/.codex/google-calendar-api-direct/client_secret.json
chmod 600 ~/.codex/google-calendar-api-direct/client_secret.json
```

7. Run OAuth:

```bash
python3 scripts/gcal_api.py auth --scopes "https://www.googleapis.com/auth/calendar.app.created"
```

Use the broader `https://www.googleapis.com/auth/calendar` scope only when you intentionally need to manage existing calendars or broader calendar resources.

## Common Commands

List calendars:

```bash
python3 scripts/gcal_api.py calendars list
```

Create a secondary calendar:

```bash
python3 scripts/gcal_api.py calendars create \
  --summary "Codex API Direct Demo" \
  --description "Created by the google-calendar-api-direct skill" \
  --time-zone Asia/Tokyo
```

Set calendar display color:

```bash
python3 scripts/gcal_api.py calendars color \
  --calendar-id "CALENDAR_ID" \
  --background "#16a765" \
  --foreground "#ffffff"
```

Create a sample event:

```bash
python3 scripts/gcal_api.py events create \
  --calendar-id "CALENDAR_ID" \
  --summary "Codex API direct sample event" \
  --start "2026-05-19T10:00:00+09:00" \
  --end "2026-05-19T10:30:00+09:00" \
  --description "Created through the direct Google Calendar API" \
  --location "Online" \
  --url "https://example.com/codex-calendar-api-direct" \
  --color-id 5 \
  --reminder-minutes 10
```

Read back events:

```bash
python3 scripts/gcal_api.py events search \
  --calendar-id "CALENDAR_ID" \
  --time-min "2026-05-19T00:00:00+09:00" \
  --time-max "2026-05-20T00:00:00+09:00" \
  --query "Codex"
```

## Public Repo Notes

- No OAuth secret files are stored in this repository.
- `.gitignore` blocks common credential, token, cache, and build artifacts.
- Destructive calendar operations are intentionally not implemented.
- Every write workflow should be followed by a read-back command before reporting success.

## License

MIT
