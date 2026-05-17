# Google Calendar API Direct Reference

## Official Endpoints

- Create calendar: `POST https://www.googleapis.com/calendar/v3/calendars`
- List calendar list entries: `GET https://www.googleapis.com/calendar/v3/users/me/calendarList`
- Patch calendar list entry: `PATCH https://www.googleapis.com/calendar/v3/users/me/calendarList/{calendarId}`
- Create event: `POST https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events`
- Search/list events: `GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events`
- Colors: `GET https://www.googleapis.com/calendar/v3/colors`

## Scopes

- Prefer `https://www.googleapis.com/auth/calendar.app.created` for app-created secondary calendars and their events.
- Use `https://www.googleapis.com/auth/calendar` when the user needs broad management of existing calendars.
- If a 403 occurs on calendar creation or update, re-auth with the broader scope only after explaining why.

## Cost and Limits

Google documents the Calendar API as free, with API quotas and Calendar product usage limits. This skill should avoid bulk writes without rate limiting and should retry politely on 429/403 rate-limit responses.

## Calendar Colors

Calendar display color is stored on the user's calendar list entry, not the calendar resource itself. To set custom RGB colors, call `calendarList.patch` with `colorRgbFormat=true` and a body that includes `backgroundColor` and `foregroundColor`.

Event colors use palette IDs from the `colors.get` event palette. Pass `colorId` on event create/update.
