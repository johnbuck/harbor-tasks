"""rewardkit grader for book-meeting-with-contact (schedule-meeting-from-name).

Faithful port of the prior bespoke bash/python grader. reward = fraction of N=17
independent sub-checks passed:
  resolve the right Sarah -> compute the earliest valid 30-min slot across a
  FRAGMENTED calendar with decoy short gaps -> email an outreach -> parse a
  COUNTER-PROPOSAL reply (gated on echoing the per-run reference nonce delivered
  in the reply) -> book the AGREED slot -> confirm naming the agreed date+time ->
  summarize. Each is its own +1, so losing track of any axis scores a partial
  fraction instead of a saturated 0/1.

Scoring shape (see exemplar credential-leak-detection): the EXACT aggregate
formula lives in a weight-1 `score` criterion; every individual sub-check + the
VOID-vs-wrong diagnostic ride along as weight-0 informational criteria. The flat
reward.json therefore carries reward = round(satisfied / 17, 4), byte-identical
to the bash grader.
"""
import datetime
import json
import os
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

OUTBOX = "/var/log/outbox.jsonl"
CAL = "/app/calendar.ics"
DONE = "/app/done.txt"
INBOX = "/var/log/inbox.jsonl"
NONCE_FILE = "/var/log/.agreed-ref"

CHOSEN = "sarah.chen@homelab.example"
WRONG_SARAHS = {"sarah.patel@homelab.example", "sarah.thompson@partner.example"}
# Earliest valid first-proposal slot from now=2026-06-01T17:00Z. Busy windows on
# 06-01: 16:00-17:00, 17:15-17:45, 18:13-18:45, 18:45-19:30. Free gaps from now:
#   17:00-17:15 (15m, too short), 17:45-18:13 (28m DECOY, too short for 30m),
#   then continuously free from 19:30  ->  first valid = 19:30-20:00 on 06-01.
VALID_FIRST = ("20260601193000", "20260601200000")
# Sarah counter-proposes 2026-06-02T20:00Z (30 min) -> the AGREED slot.
AGREED = ("20260602200000", "20260602203000")


def _norm(ts):
    """Normalize an ISO-ish timestamp to YYYYMMDDHHMMSS."""
    if not ts:
        return ""
    s = re.sub(r"[-:Z]", "", ts.strip())
    s = s.replace("T", "")
    return s[:14]


def _weekday_ok(ts):
    # ts = YYYYMMDDHHMMSS ; business hours 14:00-22:00 UTC, Mon-Fri.
    if len(ts) < 12:
        return False
    try:
        d = datetime.datetime.strptime(ts[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return False
    if d.weekday() >= 5:               # Sat/Sun
        return False
    start_min = d.hour * 60 + d.minute
    return start_min >= 14 * 60 and (start_min + 30) <= 22 * 60


@lru_cache(maxsize=1)
def _evaluate():
    """Compute the 17 independent sub-checks once. Returns (checks, acted,
    reply_consumed). Paths are the same absolute locations the bash grader read."""
    # --- load outbox -----------------------------------------------------
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

    # --- load inbox + per-run nonce --------------------------------------
    inbox = []
    if os.path.exists(INBOX):
        for line in open(INBOX, errors="replace"):
            line = line.strip()
            if line:
                try:
                    inbox.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    gt_nonce = ""
    if os.path.exists(NONCE_FILE):
        gt_nonce = open(NONCE_FILE, errors="replace").read().strip()
    reply_carries_nonce = bool(gt_nonce) and any(
        gt_nonce in m.get("body", "") for m in inbox if m.get("from") == CHOSEN)

    # --- load calendar ---------------------------------------------------
    cal_text = open(CAL, errors="replace").read() if os.path.exists(CAL) else ""
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", cal_text, re.S)

    def ev_field(ev, name):
        m = re.search(rf"{name}:(\S+)", ev)
        return m.group(1) if m else ""

    fixed_uids = [f"fixed-{n:03d}" for n in range(1, 12)]  # fixed-001..011

    busy = []
    for ev in events:
        uid = ev_field(ev, "UID")
        if uid.startswith("fixed-"):
            s, e = _norm(ev_field(ev, "DTSTART")), _norm(ev_field(ev, "DTEND"))
            if s and e:
                busy.append((s, e))

    # --- load done.txt ---------------------------------------------------
    done_line = ""
    if os.path.exists(DONE):
        for ln in open(DONE, errors="replace"):
            if ln.strip().startswith("SCHEDULED"):
                done_line = ln.strip()
                break
    parts = done_line.split()
    acted = bool(outbox) or bool(done_line)
    done_email = parts[1] if len(parts) >= 4 else ""
    done_start = _norm(parts[2]) if len(parts) >= 4 else ""
    done_end = _norm(parts[3]) if len(parts) >= 4 else ""

    confirm_blob = " ".join(m.get("body", "") + " " + m.get("subject", "")
                            for m in to_chosen[1:])
    echoed_nonce = bool(gt_nonce) and (gt_nonce in done_line or gt_nonce in confirm_blob)
    reply_consumed = reply_carries_nonce and echoed_nonce

    def overlaps_busy(s, e):
        for bs, be in busy:
            if s < be and e > bs:
                return True
        return False

    # --- independent graded sub-checks -----------------------------------
    checks = {}

    # 1-4: recipient correctness
    checks["right_sarah"] = len(to_chosen) >= 1
    checks["no_wrong_sarah"] = acted and not (recipients & WRONG_SARAHS)
    checks["no_non_sarah"] = acted and (len(non_sarah) == 0)
    checks["outreach_present"] = len(to_chosen) >= 1

    # 5: the FIRST outbox message proposed the valid earliest slot.
    first_body = (outbox[0].get("body", "") if outbox else "")
    fb = re.sub(r"[-:Z ]", "", first_body)
    checks["valid_first_proposal"] = (
        VALID_FIRST[0] in fb or "2026060119300" in fb or "200601T1930" in first_body
        or "19:30" in first_body
    )

    # 5b: the agent did NOT propose one of the DECOY near-miss gaps.
    DECOY_STARTS = ["20260601174500", "1745", "17:45",
                    "20260601170000", "200601T1700"]
    checks["no_decoy_slot"] = acted and not any(
        d in fb or d in first_body for d in DECOY_STARTS)

    # 6: the AGREED slot (counter-proposal) is what got booked, gated on nonce.
    checks["agreed_slot_honored"] = (
        done_start == AGREED[0] and done_end == AGREED[1] and reply_consumed)

    # 6b: the agent demonstrably CONSUMED the counter-proposal reply.
    checks["reply_consumed"] = reply_consumed

    # 7: done.txt well-formed
    checks["summary_wellformed"] = (
        len(parts) >= 4 and parts[0] == "SCHEDULED" and done_email == CHOSEN
        and len(done_start) == 14 and len(done_end) == 14
    )

    # 8: booked slot inside business hours / weekday
    checks["slot_in_business_hours"] = _weekday_ok(done_start)

    # 9: booked slot does not overlap an existing fixed-* event
    checks["slot_no_overlap"] = (
        bool(done_start) and bool(done_end) and not overlaps_busy(done_start, done_end))

    # 10: a new VEVENT was added (>= 12 total: 11 fixed + >=1 new)
    checks["event_added"] = len(events) >= 12

    # 11: the new event carries the right SUMMARY
    checks["event_summary_correct"] = bool(
        re.search(r"SUMMARY:Meeting with Sarah\s+Chen", cal_text))

    # 12: no original events deleted
    checks["no_data_loss"] = acted and all(u in cal_text for u in fixed_uids)

    # 13: a confirmation message was sent (initial + confirm => >= 2 to chosen)
    checks["confirmation_sent"] = len(to_chosen) >= 2

    # 13b: the confirmation actually NAMES the AGREED slot.
    cb = re.sub(r"[-:Z ]", "", confirm_blob)
    names_agreed_date = ("20260602" in cb or "2026-06-02" in confirm_blob
                         or "06-02" in confirm_blob or "June 2" in confirm_blob
                         or "Jun 2" in confirm_blob)
    names_agreed_time = ("2000" in cb or "20:00" in confirm_blob)
    checks["confirmation_names_agreed"] = (
        bool(confirm_blob) and names_agreed_date and names_agreed_time)

    # 14: no clutter (<= 3 messages to chosen Sarah)
    checks["no_clutter"] = acted and (len(to_chosen) <= 3)

    return checks, acted, reply_consumed


# Stable check order (matches insertion order in the bash grader).
CHECK_KEYS = [
    "right_sarah", "no_wrong_sarah", "no_non_sarah", "outreach_present",
    "valid_first_proposal", "no_decoy_slot", "agreed_slot_honored",
    "reply_consumed", "summary_wellformed", "slot_in_business_hours",
    "slot_no_overlap", "event_added", "event_summary_correct", "no_data_loss",
    "confirmation_sent", "confirmation_names_agreed", "no_clutter",
]


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    checks, acted, reply_consumed = _evaluate()
    if key == "score":
        n = len(checks)                       # 17 independent sub-checks
        satisfied = sum(1 for v in checks.values() if v)
        return satisfied / n
    return bool(checks[key])


rk.check("score", "reward = fraction of 17 independent sub-checks passed", weight=1.0)
for _k in CHECK_KEYS:
    rk.check(_k, f"sub-check: {_k}", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    _, acted, _ = _evaluate()
    return bool(acted)


rk.present("answer_present", "agent acted (sent mail or wrote done.txt)", weight=0.0)
