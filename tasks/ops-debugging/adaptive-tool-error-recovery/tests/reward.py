"""rewardkit grader for adaptive-tool-error-recovery (former failure-recovery-loop-01 / T6).

FAITHFUL port of the prior bespoke bash grader (the reward any submission earns is
byte-identical before/after). The formula is UNCHANGED:

    reward = 0.6*correctness + 0.4*efficiency
      correctness = (payload_ok + token_ok)/2     (0 unless a verified success exists)
      efficiency  = 0 if not recovered, else clamp((CEIL - calls)/(CEIL - IDEAL), 0, 1)
        IDEAL = 3 (clean conf-first recovery), CEIL = 18 (still flailing)
      reward      = 0 unless correctness > 0

`recovered` (=1) requires ALL of:
  * /var/log/dfetch.state carries a whole line `STATUS=success`,
  * the dfetch authenticator passes its build-pinned sha256 (bin_ok) AND
    `dfetch --verify <MSG> <NONCE>` exits 0 (verify_ok) — the HMAC nonce is genuine;
    dfetch is invoked by ABSOLUTE path so the agent cannot shadow it via PATH,
  * the ordered append-only progression log shows the error ladder ending in
    `release` (prog_ok),
  * calls >= MIN_CALLS (2).
A forged STATUS=success with no authentic nonce / no ordered progression scores 0
at ANY call count (recovered=0 -> reward 0). A poisoned (non-integer) counter is
treated as "no valid recovery, 0 calls" (calls=-1 internally -> calls_out=0),
matching the bash grader's strict-int guard.

reward.json stays a FLAT numeric dict (FOOTGUNS #2): the weight-1 `score`
criterion carries the final reward; every other signal rides along at weight 0.
"""
import hashlib
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# Absolute roots the agent's dfetch run touches. Module-level so an offline
# in-process driver can redirect them under a throwaway temp root.
STATE = Path("/var/log/dfetch.state")
COUNTER = Path("/var/log/dfetch.counter")
PROGRESSION = Path("/var/log/dfetch.progression")
DFETCH = Path("/usr/local/bin/dfetch")
# Genuine dfetch sha256, pinned at build (the trusted, post-agent, NOT
# agent-writable grader). Re-pin ONLY on a base-toolchain (gcc/libc) change.
EXPECTED_DFETCH_SHA = "b524585fb2883ffc9fc2c8f80eb4aacb1da5529c1ec152b52a4e37ddf87ac932"

RANK = {"bad-region": 1, "401": 2, "stale-lock": 3, "release": 4}
MIN_CALLS = 2
IDEAL = 3
CEIL = 18


def _state_lines() -> list:
    try:
        return STATE.read_text(errors="replace").splitlines()
    except OSError:
        return []


def _first_value(prefix: str) -> str:
    """First STATE line starting with ``prefix``, value after it.

    Mirrors ``sed -n 's/^<prefix>//p' | head -1``."""
    for line in _state_lines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return ""


def _bin_ok() -> bool:
    """Authenticator integrity pin: dfetch executable AND sha256 == pinned digest.

    Mirrors ``[ -x dfetch ] && sha256sum dfetch == EXPECTED``."""
    try:
        if not os.access(str(DFETCH), os.X_OK):
            return False
        return hashlib.sha256(DFETCH.read_bytes()).hexdigest() == EXPECTED_DFETCH_SHA
    except OSError:
        return False


@lru_cache(maxsize=4)
def _compute(workspace_str: str) -> dict:
    ws = Path(workspace_str)

    nonce = _first_value("NONCE=")
    msg = _first_value("MSG=")
    status_ok = any(line == "STATUS=success" for line in _state_lines())  # grep -qx
    bin_ok = _bin_ok()

    # HMAC authentication via the PINNED binary that owns the secret. Absent/
    # swapped binary, absent MSG, or a non-authentic nonce => verify_ok stays 0.
    verify_ok = False
    if status_ok and bin_ok and nonce and msg:
        try:
            verify_ok = subprocess.run(
                [str(DFETCH), "--verify", msg, nonce],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0
        except OSError:
            verify_ok = False

    # Correctness signals (read against the nonce dfetch actually emitted).
    payload = ws / "payload.txt"
    token = ws / "token.txt"
    payload_ok = False
    token_ok = False
    if nonce:
        try:
            payload_ok = payload.exists() and any(
                line == f"PAYLOAD: {nonce}"
                for line in payload.read_text(errors="replace").splitlines()
            )  # grep -qx "PAYLOAD: <nonce>"
        except OSError:
            payload_ok = False
        try:
            stripped = re.sub(r"[ \t\n\r\f\v]+", "", token.read_text(errors="replace"))
            token_ok = token.exists() and stripped == nonce  # tr -d '[:space:]'
        except OSError:
            token_ok = False

    answer_present = payload.exists()

    # Counter hygiene: `cat || echo 0`, then accept ONLY a strict integer; a
    # poisoned counter is 'no valid recovery' and 0 calls.
    try:
        raw = COUNTER.read_text(errors="replace").strip()
    except OSError:
        raw = "0"
    if re.fullmatch(r"-?[0-9]+", raw):
        calls = int(raw)
        calls_out = calls
    else:
        calls = -1
        calls_out = 0

    # Ordered error-progression gate: stages in canonical ladder order, ending
    # in the unavoidable 'release'.
    try:
        lines = [l.strip() for l in PROGRESSION.read_text(errors="replace").splitlines() if l.strip()]
        seq = [RANK[l] for l in lines if l in RANK]
        prog_ok = bool(seq) and seq == sorted(seq) and 4 in seq
    except OSError:
        prog_ok = False

    recovered = 1 if (status_ok and verify_ok and prog_ok and calls >= MIN_CALLS) else 0
    correctness = (int(payload_ok) + int(token_ok)) / 2.0 if recovered == 1 else 0.0
    eff = 0.0 if recovered == 0 else max(0.0, min(1.0, (CEIL - calls) / float(CEIL - IDEAL)))
    reward = 0.0 if correctness == 0 else 0.6 * correctness + 0.4 * eff

    return {
        "score": round(reward, 4),
        "correctness": round(correctness, 4),
        "efficiency": round(eff, 4),
        "recovered": float(recovered),
        "calls": float(calls_out),
        "answer_present": 1.0 if answer_present else 0.0,
        "bin_ok": 1.0 if bin_ok else 0.0,
        "verify_ok": 1.0 if verify_ok else 0.0,
        "payload_ok": 1.0 if payload_ok else 0.0,
        "token_ok": 1.0 if token_ok else 0.0,
        "prog_ok": 1.0 if prog_ok else 0.0,
    }


@rk.criterion(description="{label}")
def metric(workspace: Path, key: str, label: str):
    return _compute(str(workspace))[key]


# Weight-1 `score` carries the FLAT reward; everything else is weight-0 detail.
rk.metric("score", "reward = 0.6*correctness + 0.4*efficiency (0 unless verified recovery)", weight=1.0)
rk.metric("correctness", "(payload_ok + token_ok)/2, credited only on recovery", weight=0.0)
rk.metric("efficiency", "clamp((18-calls)/15, 0, 1); 0 unless recovered", weight=0.0)
rk.metric("recovered", "STATUS=success + HMAC verify + ordered progression + calls>=2", weight=0.0)
rk.metric("calls", "dfetch invocation count (0 if counter poisoned/absent)", weight=0.0)
rk.metric("bin_ok", "dfetch authenticator matches the build-pinned sha256", weight=0.0)
rk.metric("verify_ok", "dfetch --verify authenticated the emitted nonce", weight=0.0)
rk.metric("payload_ok", "payload.txt line equals 'PAYLOAD: <nonce>'", weight=0.0)
rk.metric("token_ok", "token.txt equals the emitted nonce", weight=0.0)
rk.metric("prog_ok", "ordered error-progression log present and ends in 'release'", weight=0.0)
# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
rk.metric("answer_present", "payload.txt persisted (VOID vs present-but-wrong)", weight=0.0)
