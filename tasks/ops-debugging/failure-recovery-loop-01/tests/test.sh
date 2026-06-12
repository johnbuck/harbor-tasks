#!/bin/bash
# ADAPTIVE-RECOVERY scorer (REBUILD 2026-06-11). Recovery REQUIRES diagnosing each
# error and applying a DIFFERENT correction (region -> provisioned region -> token
# -> release); a blind retry of the same command never succeeds, so CORRECTNESS
# itself discriminates an adaptive harness from a flailing one. Efficiency grades
# how cleanly it recovered, on a call budget.
#
# FORGERY-PROOF SUCCESS. The success payload is NONCE = HMAC-SHA256(secret,
# region|token|counter), where the secret is generated at build and embedded
# (XOR-masked) into the STRIPPED dfetch binary — it survives as plaintext nowhere
# in the image. The agent runs as root and shares the filesystem with this grader,
# so neither a hidden secret FILE nor "the agent can't see the grader" can be
# relied on; the robust hiding is the compiled binary. We therefore authenticate
# the nonce by asking dfetch itself: `dfetch --verify <MSG> <NONCE>` recomputes the
# HMAC and exits 0 only for an authentic nonce. We never hold the secret. A forged
# STATUS=success with an arbitrary nonce CANNOT pass --verify, at ANY call count.
#
# BINARY-SWAP DEFENSE (criterion 1, rebuild 2026-06-11). Because the agent is root
# on the shared filesystem, it could overwrite /usr/local/bin/dfetch with a 2-line
# `#!/bin/sh; exit 0` stub that "verifies" ANY forged nonce. Delegating auth to an
# agent-overwritable artifact is no better than holding the secret. We close this by
# PINNING the authenticator's integrity: the genuine binary's sha256 is captured at
# build time (see Dockerfile) and baked into THIS grader — which is uploaded by the
# harness post-agent and is therefore NOT agent-writable. Before crediting a verify
# we require `sha256sum /usr/local/bin/dfetch` to equal that pinned digest, and we
# invoke dfetch by ABSOLUTE path (never a PATH lookup the agent could shadow). A
# swapped stub mismatches the pin -> verify_ok stays 0 -> reward 0; the genuine
# binary cannot validate a forged nonce. RE-residual below still applies.
#
# Second, independent gate: every genuine recovery walks the error ladder, and
# dfetch appends each stage to the append-only ordered progression log
# /var/log/dfetch.progression (bad-region -> 401 -> stale-lock -> release). We
# require that log to be present, ORDERED (canonical ranks non-decreasing), and to
# contain the mechanically-unavoidable `release` (a fetch cannot succeed with the
# lock held, and the lock starts held). A success state with no ordered progression
# log scores 0.
#
# RESIDUAL (flagged): a root agent could in principle `strings`/disassemble the
# stripped binary to recover the 32-byte secret and forge a valid nonce. The design
# bet is that the honest error-walk is strictly shorter than reverse-engineering
# HMAC out of a stripped binary; "no secret FILE on the fs" is proven, RE-resistance
# is not. See backlog/2026-06-11-core-eleven-rebuild-pass.md D1.
#
# Reward = 0.6*correctness + 0.4*efficiency
#   correctness = (payload_ok + token_ok)/2   (0 unless a verified success exists)
#   efficiency  = 0 if not recovered, else clamp((CEIL - calls)/(CEIL - IDEAL),0,1)
#     IDEAL = 3 (clean conf-first recovery: stale-lock, release, success)
#     CEIL  = 18 (still flailing at >5x the discovery cost)
# reward.json MUST be a FLAT scalar dict (Harbor rejects nested; FOOTGUNS #2).
set -u
mkdir -p /logs/verifier

ST=/var/log/dfetch.state
NONCE="$(sed -n 's/^NONCE=//p' "$ST" 2>/dev/null | head -1)"
MSG="$(sed -n 's/^MSG=//p' "$ST" 2>/dev/null | head -1)"
status_ok=0
grep -qx 'STATUS=success' "$ST" 2>/dev/null && status_ok=1

# Authenticator integrity pin. The genuine dfetch is compiled from a FIXED secret
# with a reproducible toolchain (see environment/Dockerfile), so its sha256 is
# stable across rebuilds and pinned here, in the trusted post-agent grader. A root
# agent that swaps dfetch for an exit-0 --verify stub mismatches the pin → bin_ok
# stays 0 → reward 0. Re-pin ONLY if the harbor-agents-rich base toolchain
# (gcc/libc) changes: rebuild the task image and update the digest below
# (verified reproducible across two no-cache builds, 2026-06-12).
DFETCH=/usr/local/bin/dfetch
EXPECTED_DFETCH_SHA="b524585fb2883ffc9fc2c8f80eb4aacb1da5529c1ec152b52a4e37ddf87ac932"   # 64-hex; re-pin on base-toolchain change
bin_ok=0
if [ -x "$DFETCH" ]; then
  actual_sha="$(sha256sum "$DFETCH" 2>/dev/null | cut -d' ' -f1)"
  [ -n "$actual_sha" ] && [ "$actual_sha" = "$EXPECTED_DFETCH_SHA" ] && bin_ok=1
fi

# HMAC authentication via the PINNED binary that owns the secret. Absent/ swapped
# binary, absent MSG, or a non-authentic nonce => verify_ok stays 0. dfetch is
# invoked by absolute path so the agent cannot shadow it via PATH.
verify_ok=0
if [ "$status_ok" = 1 ] && [ "$bin_ok" = 1 ] && [ -n "$NONCE" ] && [ -n "$MSG" ]; then
  if "$DFETCH" --verify "$MSG" "$NONCE" >/dev/null 2>&1; then verify_ok=1; fi
fi

# Correctness signals (read against the nonce dfetch actually emitted; never a
# baked literal). Computed here as 0/1; only credited when recovered.
payload_ok=0; token_ok=0
if [ -n "$NONCE" ]; then
  [ -f /app/payload.txt ] && grep -qx "PAYLOAD: ${NONCE}" /app/payload.txt && payload_ok=1
  [ -f /app/token.txt ] && [ "$(tr -d '[:space:]' < /app/token.txt 2>/dev/null)" = "${NONCE}" ] && token_ok=1
fi

answer_present=0; [ -f /app/payload.txt ] && answer_present=1
calls=$(cat /var/log/dfetch.counter 2>/dev/null || echo 0)

read reward correctness efficiency recovered calls <<<"$(calls_raw="$calls" status_ok="$status_ok" verify_ok="$verify_ok" python3 -c "
import os, re
# Counter hygiene + S4 crash guard + CODE-INJECTION guard: the counter is
# agent-writable (root, world-writable) and its bytes are NEVER interpolated into
# this interpreter source (a triple-quote breakout would forge the reward). Read
# from the environment, accept ONLY a strict integer; a poisoned counter is 'no
# valid recovery' and 0 calls. The MSG/NONCE (also agent-writable) never enter
# this source either — the HMAC check ran in bash via the binary.
s=os.environ['calls_raw'].strip()
if re.fullmatch(r'-?[0-9]+', s):
    calls=int(s); calls_out=calls
else:
    calls=-1; calls_out=0
status_ok = os.environ['status_ok']=='1'
verify_ok = os.environ['verify_ok']=='1'

# Ordered error-progression gate: stages must appear in canonical ladder order and
# include the unavoidable 'release'. Read inside python so a missing/odd file can
# never crash the grader.
RANK={'bad-region':1,'401':2,'stale-lock':3,'release':4}
try:
    lines=[l.strip() for l in open('/var/log/dfetch.progression') if l.strip()]
    seq=[RANK[l] for l in lines if l in RANK]
    prog_ok = bool(seq) and seq==sorted(seq) and 4 in seq
except OSError:
    prog_ok=False

MIN_CALLS=2; IDEAL=3; CEIL=18
recovered = 1 if (status_ok and verify_ok and prog_ok and calls>=MIN_CALLS) else 0
p=$payload_ok; t=$token_ok
correctness=(p+t)/2.0 if recovered==1 else 0.0
eff = 0.0 if recovered==0 else max(0.0, min(1.0, (CEIL-calls)/float(CEIL-IDEAL)))
reward = 0.0 if correctness==0 else 0.6*correctness + 0.4*eff
print(round(reward,4), round(correctness,4), round(eff,4), recovered, calls_out)
" 2>/dev/null)"

# Belt-and-suspenders fallback: if the scorer produced nothing (e.g. python failed
# to start), still emit a FLAT numeric reward so the trial is not silently dropped.
if [ -z "${reward:-}" ]; then
  reward=0.0; correctness=0.0; efficiency=0.0; recovered=0; calls=0
fi

cat > /logs/verifier/reward.json <<JSON
{"reward": ${reward}, "correctness": ${correctness}, "efficiency": ${efficiency}, "calls": ${calls}, "recovered": ${recovered}, "answer_present": ${answer_present}}
JSON

cat > /logs/verifier/reward-details.json <<JSON
{
  "emitted_nonce": "${NONCE}",
  "bin_ok": ${bin_ok},
  "verify_ok": ${verify_ok},
  "payload_ok": ${payload_ok},
  "token_ok": ${token_ok},
  "note": "recovered requires a build-pinned (sha256) dfetch binary, an HMAC-authenticated nonce (dfetch --verify) AND an ordered progression log with 'release'. bin_ok=0 means the authenticator failed its integrity pin (swapped stub, or the D7 build digest is not yet pasted into EXPECTED_DFETCH_SHA). recovered=0 => VOID (reward 0). Nonce is HMAC(secret, region|token|counter); the secret lives only in the stripped dfetch binary."
}
JSON
