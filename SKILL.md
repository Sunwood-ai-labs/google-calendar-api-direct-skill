---
name: google-calendar-api-direct
description: Use when Codex needs to call the Google Calendar API directly instead of the built-in connector, especially to create secondary calendars, set calendar colors, list calendars, create events on a specific calendar, or verify Calendar API writes with local OAuth credentials.
---

# Google Calendar API Direct

## Overview

Use this skill when the built-in Google Calendar connector is not enough, especially for calendar-level operations such as creating a new calendar. Prefer the connector for ordinary event reads/writes when it supports the task; use this direct API path for secondary-calendar setup, calendar colors, bulk seed data, and reproducible local automation.

Google Calendar API usage is free, but it is quota-limited. Avoid high-rate loops and read back every write before reporting success.

## Local Tool

Use `scripts/gcal_api.py` from this skill directory. It stores OAuth material outside the repository under:

- `~/.codex/google-calendar-api-direct/client_secret.json`
- `~/.codex/google-calendar-api-direct/token.json`

Never paste OAuth secrets into chat. Keep downloaded client JSON local.

## Setup Workflow

1. In Google Cloud Console, create or select a project.
2. Enable **Google Calendar API**.
3. Configure OAuth consent for an external or internal desktop app as appropriate.
4. Create an OAuth client of type **Desktop app**.
5. Download the client JSON and place it at the client secret path above.
6. Run:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py auth
```

If the skill is installed somewhere else, run the same command from that skill directory as:

```bash
python3 scripts/gcal_api.py auth
```

For personal/local use, request the narrowest useful scope:

- `https://www.googleapis.com/auth/calendar.app.created` can create secondary calendars and manage events on calendars the app created.
- `https://www.googleapis.com/auth/calendar` is broader and can manage all calendars the user can access. Use only when the task needs existing calendar management.

## Common Commands

List calendars:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py calendars list
```

Create a calendar:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py calendars create --summary "Codex Demo" --description "Created by Codex" --time-zone Asia/Tokyo
```

Set the calendar display color:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py calendars color --calendar-id CALENDAR_ID --background "#16a765" --foreground "#ffffff"
```

Create an event:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py events create --calendar-id CALENDAR_ID --summary "Codex Sample" --start "2026-05-18T10:00:00+09:00" --end "2026-05-18T10:30:00+09:00" --description "Sample event" --location "Online" --color-id 5
```

Search events in a bounded window:

```bash
python3 /Users/admin/.codex/skills/google-calendar-api-direct/scripts/gcal_api.py events search --calendar-id CALENDAR_ID --time-min "2026-05-18T00:00:00+09:00" --time-max "2026-05-19T00:00:00+09:00" --query "Codex"
```

## Safety

- Before creating OAuth clients, enabling APIs, or accepting permission prompts via Computer Use, follow the Computer Use confirmation policy.
- Keep `client_secret.json`, token files, and `.env` files out of the skill repository. They belong under `~/.codex/google-calendar-api-direct/` or another explicitly configured local path.
- For destructive operations, prefer not to implement deletion unless the user explicitly asks. If deletion is added later, require a clear calendar ID and a final confirmation.
- When creating sample data, include `Codex` in summaries and descriptions so test artifacts are easy to find.
- Always report exact calendar IDs, event IDs, dates, time zones, and the verification command/result.

## References

Read `references/calendar-api.md` when the task requires API endpoints, scopes, color behavior, or GCP setup details.
