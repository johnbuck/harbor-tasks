#!/bin/bash
# Graded verifier for schedule-meeting-from-name.
# reward = fraction of N independent sub-checks passed. The task threads state
# across several steps (resolve referent -> compute earliest valid slot ->
# email -> parse a COUNTER-PROPOSAL reply -> book the AGREED slot -> confirm ->
# summarize). Each of those is its own +1, so a harness that loses track of the
# counter-proposal, mis-computes the earliest slot, double-books, or clutters
# the outbox scores a partial fraction instead of a saturated 0/1.
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json, os, re

OUTBOX = "/var/log/outbox.jsonl"
CAL = "/app/calendar.ics"
DONE = "/app/done.txt"

CHOSEN = "sarah.chen@homelab.example"
WRONG_SARAHS = {"sarah.patel@homelab.example", "sarah.thompson@partner.example"}
# Earliest valid first-proposal slot from now=2026-06-01T17:00Z. Busy windows on
# 06-01: 16:00-17:00, 17:15-17:45, 18:13-18:45, 18:45-19:30. Free gaps from now:
#   17:00-17:15 (15m, too short), 17:45-18:13 (28m DECOY, too short for 30m),
#   then continuously free from 19:30  ->  first valid = 19:30-20:00 on 06-01.
VALID_FIRST = ("20260601193000", "20260601200000")
# Sarah counter-proposes 2026-06-02T20:00Z (30 min) -> the AGREED slot.
AGREED = ("20260602200000", "20260602203000")

def norm(ts):
    """Normalize an ISO-ish timestamp to YYYYMMDDHHMMSS."""
    if not ts:
        return ""
    s = re.sub(r"[-:Z]", "", ts.strip())
    s = s.replace("T", "")
    return s[:14]

# --- load outbox ---------------------------------------------------------
outbox = []
if os.path.exists(OUTBOX):
    for line in open(OUTBOX, errors="replace"):
        line = line.strip()
        if line:
            try:
                outbox.append(json.loads(line))
            except json.JSONDecodeError:
                pass

to_chosen = [m for m in outbox if m.get("to") == CHOSEN]
recipients = {m.get("to") for m in outbox}
non_sarah = {r for r in recipients if not (r or "").lower().startswith("sarah.")}

# --- load calendar -------------------------------------------------------
cal_text = open(CAL, errors="replace").read() if os.path.exists(CAL) else ""
events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", cal_text, re.S)
def ev_field(ev, name):
    m = re.search(rf"{name}:(\S+)", ev)
    return m.group(1) if m else ""
fixed_uids = [f"fixed-{n:03d}" for n in range(1, 12)]  # fixed-001..011

# Original busy windows (for overlap check) — only the fixed-* events.
busy = []
for ev in events:
    uid = ev_field(ev, "UID")
    if uid.startswith("fixed-"):
        s, e = norm(ev_field(ev, "DTSTART")), norm(ev_field(ev, "DTEND"))
        if s and e:
            busy.append((s, e))

# --- load done.txt -------------------------------------------------------
done_line = ""
if os.path.exists(DONE):
    for ln in open(DONE, errors="replace"):
        if ln.strip().startswith("SCHEDULED"):
            done_line = ln.strip()
            break
parts = done_line.split()
# The agent actually DID something (sent mail or wrote done.txt). Absence-of-bad
# checks below are gated on this so a pure no-op cannot floor on inaction.
acted = bool(outbox) or bool(done_line)
done_email = parts[1] if len(parts) >= 4 else ""
done_start = norm(parts[2]) if len(parts) >= 4 else ""
done_end = norm(parts[3]) if len(parts) >= 4 else ""

def weekday_ok(ts):
    # ts = YYYYMMDDHHMMSS ; business hours 14:00-22:00 UTC, Mon-Fri.
    if len(ts) < 12:
        return False
    import datetime
    try:
        d = datetime.datetime.strptime(ts[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return False
    if d.weekday() >= 5:               # Sat/Sun
        return False
    start_min = d.hour * 60 + d.minute
    return start_min >= 14 * 60 and (start_min + 30) <= 22 * 60

def overlaps_busy(s, e):
    for bs, be in busy:
        if s < be and e > bs:
            return True
    return False

# --- independent graded sub-checks --------------------------------------
checks = {}

# 1-4: recipient correctness
checks["right_sarah"]    = len(to_chosen) >= 1
checks["no_wrong_sarah"] = acted and not (recipients & WRONG_SARAHS)
checks["no_non_sarah"]   = acted and (len(non_sarah) == 0)
checks["outreach_present"] = len(to_chosen) >= 1

# 5: the FIRST outbox message proposed the valid earliest slot. Accept either
#    compact or punctuated ISO in the body, and the "19:30" wall-clock form.
first_body = (outbox[0].get("body", "") if outbox else "")
fb = re.sub(r"[-:Z ]", "", first_body)
checks["valid_first_proposal"] = (
    VALID_FIRST[0] in fb or "2026060119300" in fb or "200601T1930" in first_body
    or "19:30" in first_body
)

# 5b: the agent did NOT propose one of the DECOY near-miss gaps in its first
#     outreach. The calendar has tempting short gaps before 19:30:
#       17:00-17:15 (15m), 17:45-18:13 (28m). A naive "first free gap" scanner
#     grabs the 17:45 window, which is too short for a 30-min meeting and is a
#     hard fail. The proposal must avoid all decoy start-times.
DECOY_STARTS = ["20260601174500", "1745", "17:45",
                "20260601170000", "200601T1700"]
checks["no_decoy_slot"] = acted and not any(d in fb or d in first_body for d in DECOY_STARTS)

# 6: the AGREED slot (the counter-proposal) is what got booked in done.txt.
checks["agreed_slot_honored"] = (done_start == AGREED[0] and done_end == AGREED[1])

# 7: done.txt well-formed (SCHEDULED <email> <start> <end>, right email)
checks["summary_wellformed"] = (
    len(parts) >= 4 and parts[0] == "SCHEDULED" and done_email == CHOSEN
    and len(done_start) == 14 and len(done_end) == 14
)

# 8: booked slot inside business hours / weekday
checks["slot_in_business_hours"] = weekday_ok(done_start)

# 9: booked slot does not overlap an existing fixed-* event
checks["slot_no_overlap"] = bool(done_start) and bool(done_end) and not overlaps_busy(done_start, done_end)

# 10: a new VEVENT was added (>= 12 total: 11 fixed + >=1 new)
checks["event_added"] = len(events) >= 12

# 11: the new event carries the right SUMMARY
checks["event_summary_correct"] = bool(re.search(r"SUMMARY:Meeting with Sarah\s+Chen", cal_text))

# 12: no original events deleted
checks["no_data_loss"] = acted and all(u in cal_text for u in fixed_uids)

# 13: a confirmation message was sent (initial + confirm => >= 2 to chosen)
checks["confirmation_sent"] = len(to_chosen) >= 2

# 13b: the confirmation actually NAMES the AGREED slot (date 2026-06-02 and the
#      20:00 start), not the originally-proposed 06-01 time. A harness that
#      "confirms" but re-states its own first proposal fails this. Scan all
#      messages to the chosen Sarah AFTER the first outreach.
confirm_blob = " ".join(m.get("body", "") + " " + m.get("subject", "")
                        for m in to_chosen[1:])
cb = re.sub(r"[-:Z ]", "", confirm_blob)
names_agreed_date = ("20260602" in cb or "2026-06-02" in confirm_blob
                     or "06-02" in confirm_blob or "June 2" in confirm_blob
                     or "Jun 2" in confirm_blob)
names_agreed_time = ("2000" in cb or "20:00" in confirm_blob)
checks["confirmation_names_agreed"] = bool(confirm_blob) and names_agreed_date and names_agreed_time

# 14: no clutter (<= 3 messages to chosen Sarah)
checks["no_clutter"] = acted and (len(to_chosen) <= 3)

# --- aggregate -----------------------------------------------------------
N = len(checks)
satisfied = sum(1 for v in checks.values() if v)
reward = round(satisfied / N, 4)
correctness = 1 if satisfied == N else 0

out = {
    "reward": reward,
    "correctness": correctness,
    "satisfied": satisfied,
    "n_checks": N,
    "n_messages": len(outbox),
    "n_to_chosen": len(to_chosen),
    "answer_present": 1 if acted else 0,
}
print(json.dumps(out))
PY

# S4 crash guard: if the grader above crashed before emitting a parseable
# reward.json, write a flat numeric fallback so Harbor scores 0 rather than
# silently DROPPING the trial (FOOTGUNS #2).
[ -s /logs/verifier/reward.json ] || echo '{"reward":0.0}' > /logs/verifier/reward.json
