#!/bin/bash
# Oracle: picks Sarah Chen (highest shared_meetings_last_30d + "weekly direct
# manager" note). Earliest valid 30-min slot from now=2026-06-01T17:00Z is
# 19:30-20:00 (17:00-17:15 and 17:45-18:00 are only 15-min gaps; 18:00-19:30 is
# the architecture review). Proposes that, ticks the inbox, then HONORS Sarah's
# counter-proposal of 2026-06-02T20:00Z. Books the AGREED slot, confirms,
# writes done.txt with the agreed slot.
set -u

SARAH=sarah.chen@homelab.example
PROPOSED_START=20260601T193000Z   # our valid earliest first-proposal

send-email \
    --to "$SARAH" \
    --subject "Quick sync — 30 min?" \
    --body "Hey Sarah — wanted to grab 30 minutes. Earliest I have free is 2026-06-01T19:30Z (30 min). Lmk if that works. Thanks, Alex"

# Force the responder to process pending outbox immediately
tick-inbox --once

# Read the reply (she counter-proposes 2026-06-02T20:00Z)
REPLY=$(inbox-poll --from "$SARAH" | tail -1)
echo "got reply: $REPLY" >&2

# Honor her counter-proposed slot.
AGREED_START=20260602T200000Z
AGREED_END=20260602T203000Z

# Append the new calendar event for the AGREED slot
cat >> /app/calendar.ics <<EOF
BEGIN:VEVENT
UID:agent-meeting-001@homelab.example
DTSTART:${AGREED_START}
DTEND:${AGREED_END}
SUMMARY:Meeting with Sarah Chen
END:VEVENT
EOF

# Confirmation email naming the agreed slot
send-email \
    --to "$SARAH" \
    --subject "Confirmed: sync on 2026-06-02" \
    --body "Great — 2026-06-02T20:00Z works. Booked us in for 30 minutes. See you then."

# Summary uses the AGREED slot
echo "SCHEDULED $SARAH $AGREED_START $AGREED_END" > /app/done.txt
