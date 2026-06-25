---
status: IMPLEMENTED
epic: E4
date: 2026-06-10
---

# Overnight verifier-integrity work — decisions + open questions (for morning review)

**Context.** Continued the verifier-integrity rollout unsupervised overnight, with
two operator directives: *make north-star-aligned calls, don't block on questions,
document them for the morning* and *avoid spending OpenRouter credits*. Everything
below was validated with the **free oracle** only — no LLM/harness runs were
launched. All work is **uncommitted** on `main` for your review.

See `NORTH_STAR.md` (created tonight — there wasn't one) for the value hierarchy I
used to make these calls.

---

## What I did (done + oracle-validated)

1. **`test-authoring/unit-tests-01` — closed an answer-key leak.** The 4 grading
   mutants were baked agent-readable at `/opt/canonical/mutants/`, leaking exactly
   which behaviors are scored (a capable agent could read them and write targeted
   tests — KILL-test fail). Fix: **relocated mutants `environment/` → `tests/`**
   (Harbor uploads `tests/` only *after* the agent runs). Repointed the grader to
   `/tests/mutants/`. Oracle: reward 1.0, 4/4 killed, gates pass. *Honest behavior
   unchanged; this is purely a leak fix.*

2. **`ops-debugging/failure-recovery-loop-01` — closed the KILL-test shortcut on a
   PROVEN discriminator.** The success payload was a plaintext literal
   `PAYLOAD: hgr-7842-OK` inside the agent-readable `dfetch` script — a single
   `grep dfetch` yielded the answer, letting a capable agent skip the entire
   diagnose-and-adapt loop. Fix: **`dfetch` now DERIVES the payload from the session
   token** (`sha256(token)[:11]`) at emit time instead of storing a literal, so no
   single file-read leaks it. The grader (in `tests/`, agent-invisible) checks the
   precomputed expected value. Oracle: reward 1.0, correctness 1.0, **calls 2 —
   identical to before**, which is the key safety property: *honest agents run
   `dfetch` and get whatever it emits, so their trajectories (and the discrimination)
   are unchanged; only the emitted/expected string moved in lockstep.*

3. **`NORTH_STAR.md`** — distilled the thesis, KILL test, no-telegraphing, pass^k,
   fair-comparison invariants, scoring integrity, and cost discipline into one
   canonical decision anchor (you asked if it existed — it didn't).

4. Earlier in the session (recap): 54-task audit, rollout spec, rewardkit **baked**
   into the verifier image, FOOTGUNS #42–44, roadmap.

## Decisions I made (north-star rationale)

- **Fixed the two honest-shortcut leaks, skipped the adversarial-forge tasks.**
  `tool-sprawl-precision-01`, `tool-selection-01`, `browser-find-fact-01`,
  `prompt-injection-resistance-01` trust a `chmod 666` log / plantable marker. But
  this eval measures **honest** harnesses, which produce genuine signals and never
  fabricate logs — so converting these is speculative hardening against an adversary
  the eval doesn't contain (NORTH_STAR: no speculative work, simplicity). The
  honest-shortcut leaks (a capable agent legitimately reading a baked answer) are
  the real KILL-test failures, so those got the effort.

- **Did NOT touch `failure-recovery`'s discrimination logic, only the answer
  representation.** Changing a proven discriminator I can't re-baseline tonight
  (no paid runs) is the one thing NORTH_STAR says not to do. The token-derivation is
  provably behavior-preserving for honest agents (oracle confirms the identical
  2-call path), so it's the safe version.

- **Deferred `schedule-meeting-from-name-01`** (see open questions) — its fix is not
  safe to do unsupervised.

## Open questions (for the morning — none block the safe work above)

1. **Re-baseline `failure-recovery-loop-01`.** The token-derivation should preserve
   the oc-vs-he gap (honest behavior is unchanged), but "should" needs an **n≥3
   paid run** to confirm the magnitude survived. I did not spend the credits.
   → *Run it supervised, or trust the behavior-preservation argument?*

2. **Is the `failure-recovery` fix "airtight enough"?** It passes the KILL test as
   literally stated (no single file-read leaks the answer), but a determined root
   agent can still read the token + replicate the hash (a 3-step shortcut). The
   airtight version needs a **privilege boundary** — a stateful localhost sidecar
   holding an in-memory per-trial secret that only yields after the real handshake.
   That's a bigger, supervised change. → *Is KILL-test-literal sufficient, or build
   the sidecar?*

3. **`schedule-meeting-from-name-01` — deferred.** The agreed slot is a literal in
   the agent-readable `/opt/real-world-sim/responder.py`; an agent can read it
   instead of negotiating. Because the agent runs as **root**, I cannot hide the
   file — the real fix is to run the responder as an **isolated compose sidecar**
   (source unreadable by the agent) or make the slot **dynamic** from the
   negotiation. 16 grade steps, not a proven discriminator, real-world-sim infra →
   too risky to redesign unsupervised. → *Sidecar redesign, or accept + document?*

4. **The root-agent finding (the deepest one).** In the thin single-container model
   the agent runs shell as the same user that owns everything, so **no in-container
   secret is hideable** and no in-container log is un-forgeable. Tonight's fixes
   raise the bar within that constraint; truly closing forge/shortcut surfaces would
   require running the **agent as non-root** (enabling real privilege boundaries for
   verifier secrets). That's a large infra change and interacts with the
   browser's run-as-root no-sandbox. → *Worth exploring, or live with the
   honest-harness framing (we only need honest agents not to shortcut)?*

5. **Wave-3 rewardkit-only modernization** (recall-style conversation tasks +
   deterministic single-graders): skipped as low-value — no integrity gain, pure
   per-criterion observability, and multistep (6–19 steps) makes it costly.
   → *Confirm skip, or is the `harbor view` per-criterion breakdown worth it?*

6. **Commit strategy.** Everything is uncommitted on `main`. Per the repo rule I did
   not commit. → *Branch + commit these validity fixes, or keep reviewing in the
   working tree?*

## Net effect on the thesis

Two KILL-test failures closed (one of them a proven discriminator), zero credits
spent, zero changes to honest-agent behavior. The `#81` verdict is now gated on a
supervised re-baseline of `failure-recovery` rather than on an undiscovered
validity hole — a strictly better place to be.
