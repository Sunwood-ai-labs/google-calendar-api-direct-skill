import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import gcal_api  # noqa: E402


class GcalApiTests(unittest.TestCase):
    def test_parse_scopes_accepts_spaces_and_commas(self):
        scopes = gcal_api.parse_scopes("scope-a, scope-b scope-c")
        self.assertEqual(scopes, ["scope-a", "scope-b", "scope-c"])

    def test_default_credential_paths_are_outside_repo(self):
        root = str(ROOT)
        self.assertFalse(str(gcal_api.CLIENT_SECRET_PATH).startswith(root))
        self.assertFalse(str(gcal_api.TOKEN_PATH).startswith(root))

    def test_calendar_color_uses_patch(self):
        captured = {}

        def fake_api(method, path, body=None, query=None):
            captured.update({"method": method, "path": path, "body": body, "query": query})
            return {"ok": True}

        args = type(
            "Args",
            (),
            {
                "calendar_id": "demo@example.com",
                "background": "#16a765",
                "foreground": "#ffffff",
            },
        )()

        with mock.patch.object(gcal_api, "api", fake_api), mock.patch("sys.stdout"):
            gcal_api.calendars_color(args)

        self.assertEqual(captured["method"], "PATCH")
        self.assertEqual(captured["path"], "/users/me/calendarList/demo%40example.com")
        self.assertEqual(captured["body"], {"backgroundColor": "#16a765", "foregroundColor": "#ffffff"})
        self.assertEqual(captured["query"], {"colorRgbFormat": "true"})


if __name__ == "__main__":
    unittest.main()
