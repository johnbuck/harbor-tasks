#!/usr/bin/env python3
"""Templated inbox responder. Polls /var/log/outbox.jsonl every 2 seconds;
when it sees a new message addressed to one of the simulated peers, it
appends a reply to /var/log/inbox.jsonl after a fixed 5-second delay.

Reply templates per recipient (only Sarah Chen produces a real working
slot — Sarah Patel and Sarah Thompson reply with bounce-style messages
that should signal "wrong person" to a competent agent).

Tracks which outbox messages have already been processed via a position
file at /var/log/.outbox.cursor.
"""

from __future__ import annotations

import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

OUTBOX = Path("/var/log/outbox.jsonl")
INBOX = Path("/var/log/inbox.jsonl")
CURSOR = Path("/var/log/.outbox.cursor")
# Per-run ground-truth nonce file. Written at REPLY time (so it exists only AFTER
# the agent emailed the chosen Sarah), it is the verifier's source of truth that
# the booking was driven by the delivered reply — not by reading a static file.
NONCE_FILE = Path("/var/log/.agreed-ref")
DELAY = 5  # seconds before reply lands
POLL = 2

# Reply templates keyed by recipient. {"agree_slot": ...} = the message
# proposes a slot from any the outbox suggests; {"bounce": ...} = polite
# decline; {"silent": ...} = no reply at all.
TEMPLATES = {
    "sarah.chen@homelab.example": {
        "subject_prefix": "Re: ",
        "body": (
            "Thanks for the proposal, but that exact time doesn't work for me — "
            "I have a hard stop right after. Could we instead do "
            "{agreed} (30 minutes)? That window is clear for me. Please quote "
            "reference {nonce} in your confirmation so I can match it to this "
            "thread. I'll plan on it unless I hear otherwise. — Sarah"
        )
    },
    "sarah.patel@homelab.example": {
        "subject_prefix": "Re: ",
        "body": "Hi — I think you may have the wrong Sarah. I'm Sarah Patel, we met at the meetup; I'm not in the company. Did you mean Sarah Chen?"
    },
    "sarah.thompson@partner.example": {
        "subject_prefix": "Out of office: ",
        "body": "I'm away from email this week. Please contact the Acme support team for non-urgent requests."
    },
}


def _user() -> str:
    return Path("/etc/sim/user-email").read_text().strip()


def _agreed() -> str:
    """The counter-proposal slot, kept out of this world-readable source. The
    agent runs as root so file mode can't hide it; the booking is instead gated
    on the per-run nonce minted below, so reading this value alone earns nothing."""
    try:
        return Path("/etc/sim/agreed-slot").read_text().strip()
    except OSError:
        return ""


def _new_nonce() -> str:
    """A fresh per-run reference the verifier requires the agent to echo back. It
    is generated only when a reply is actually produced, so it appears in no
    pre-baked file."""
    return "REF-" + secrets.token_hex(4)


def process(lines: list[str], me: str) -> None:
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        tmpl = TEMPLATES.get(msg.get("to"))
        if not tmpl:
            continue
        # Schedule the reply
        time.sleep(DELAY)
        body = tmpl["body"]
        if "{agreed}" in body or "{nonce}" in body:
            nonce = _new_nonce()
            body = body.format(agreed=_agreed(), nonce=nonce)
            # Record the per-run nonce as the verifier's ground truth (runtime-
            # only; created here, after the agent emailed).
            try:
                NONCE_FILE.write_text(nonce)
            except OSError:
                pass
        reply = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "from": msg["to"],
            "to": me,
            "cc": [],
            "subject": tmpl["subject_prefix"] + msg.get("subject", ""),
            "body": body,
        }
        with INBOX.open("a") as f:
            f.write(json.dumps(reply) + "\n")


def main() -> None:
    me = _user()
    OUTBOX.parent.mkdir(parents=True, exist_ok=True)
    OUTBOX.touch()
    INBOX.touch()
    CURSOR.touch()
    while True:
        pos = int(CURSOR.read_text() or "0")
        size = OUTBOX.stat().st_size
        if size > pos:
            with OUTBOX.open() as f:
                f.seek(pos)
                new_lines = f.readlines()
            CURSOR.write_text(str(size))
            if new_lines:
                process(new_lines, me)
        time.sleep(POLL)


if __name__ == "__main__":
    # One-shot mode if invoked with --once (used by `tick-inbox`).
    import sys
    if "--once" in sys.argv:
        me = _user()
        OUTBOX.touch(); INBOX.touch(); CURSOR.touch()
        pos = int(CURSOR.read_text() or "0")
        with OUTBOX.open() as f:
            f.seek(pos)
            new_lines = f.readlines()
        CURSOR.write_text(str(OUTBOX.stat().st_size))
        # In --once mode, no delay between observation and reply. (Rebind the
        # module-global via globals() — a bare `global` here is a SyntaxError
        # because DELAY is already read at module scope above.)
        globals()["DELAY"] = 0
        process(new_lines, me)
    else:
        main()
