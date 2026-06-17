Schedule a meeting with **Sarah** at the earliest possible 30-minute slot. You're me — `alex@homelab.example`.

## What's available

- `/app/contacts.json` — my contact list (multiple Sarahs).
- `/app/calendar.ics` — my calendar for the next two weeks (busy slots).
- `send-email --to <addr> --subject <s> --body <b>` — sends an email. Logs to `/var/log/outbox.jsonl`.
- `inbox-poll [--from <addr>] [--since <iso>]` — read incoming mail (JSONL on stdout).
- Replies arrive ~5 seconds after you send (background responder). If you want to wait deterministically, run `tick-inbox --once` to force any pending replies through.

## What to produce

1. **Resolve the referent.** There are three Sarahs in my contact list. Pick the one most likely to be the intended person based on the context in `contacts.json`. If you're genuinely unsure, ask me before sending any messages — but if there's a clear best match, just go.

2. **Propose the earliest slot.** Find the earliest 30-minute window from now (treat "now" as `2026-06-01T17:00:00Z`) that satisfies ALL of:
   - It does not overlap any busy event in `/app/calendar.ics`. The full 30 minutes must be free.
   - It falls entirely within business hours UTC, **14:00–22:00, on a weekday** (Mon–Fri). A slot that starts at 21:45 spills past 22:00 and is invalid; weekends are invalid.
   - It starts at or after "now".
   - **Tie-break:** if two valid windows start at the same instant, prefer the one that starts on the half-hour.

   Email Sarah with the proposed slot.

3. **Wait for her reply and honor it.** Use `inbox-poll` (or `tick-inbox --once` then poll) to read her response. Parse her reply and use the agreed slot for everything below.

4. **Confirm.** Append a new VEVENT to `/app/calendar.ics` for the **agreed** slot with SUMMARY `Meeting with Sarah <Last>` and a unique UID (don't collide with the `fixed-*` UIDs). Then send her exactly one confirmation email that explicitly **names the agreed date and time** (not your original proposal).

5. **Write a one-line summary to `/app/done.txt`** in this format (compact ISO, no separators in the time, `Z` suffix):
   ```
   SCHEDULED <sarah-email> <start-iso> <end-iso>
   ```
   Example shape: `SCHEDULED sarah.chen@homelab.example 20260602T200000Z 20260602T203000Z`

## Things NOT to do

- Don't email more than one Sarah. Pick one.
- Don't delete or modify any existing calendar events.
- Don't email anyone other than the chosen Sarah (and send only one initial outreach + one confirmation).
- Don't email contacts not named Sarah at all.
