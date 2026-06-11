---
status: IN PROGRESS
epic: E4
date: 2026-06-10
---

# Core-eleven remediation — make the load-bearing suite actually measure the harness

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-10
**Status:** IMPLEMENTED 2026-06-10 — all 11 tasks reworked, substrate symmetric
(hindsight-only), threading landed + proven, image rebuilt, oracle 11/11, and the
**n=5 grid shows the suite discriminates (effective Δ 0.188, all 7 categories split
≥10%).** Remaining follow-ups (not blockers): harden context-rot chains (weakest at
Δ−0.10), trim the dead recall-wipe path, fix the `infisical-identity.env` doc
reference. Move to `done/` once those land.
**Origin / triggered-by:** operator asked for a fresh adversarial review of the
eleven core tasks (`configs/core-suite.yaml`) under the lens "do these measure the
HARNESS, and do they reflect real-world work." 11 parallel adversaries returned
**zero clean KEEPs** (3 hard KILL, 8 REWORK). This spec is the remediation plan.
**Predecessor:** `2026-06-01-adversarial-review.md` (the first pass; many of these
tasks were flagged REWORK there and the core-suite was selected on 2026-06-03
**without** re-verifying the fixes landed — this review found most did not).

## Problem

As wired today the core suite cannot attribute a score gap to the harness. Every
task risks saturating (1.0/1.0 **or** 0.0/0.0), being model-solvable, or
manufacturing fake signal through grader artifacts. Two findings are structural
(affect the whole suite); the rest are per-task. All bypasses below were
**re-verified live** on 2026-06-10 (a second agent re-ran the exploits) — 5 of 5
hold.

### Structural finding 1 — the context pillar is untestable under the current runner

Every Harbor step invokes the harness **fresh, with no session-continuation flag**:
`openclaw agent --local --json --message <…>` (`lib/openclaw_thin.py:118-125`) and
`hermes --yolo chat -q "$INSTRUCTION" -Q` (`lib/hermes_thin.py:105-110`). There is
**no single growing conversation** across steps.

- The container **does** persist across steps — `MultiStepTrial._run`
  (`harbor/src/harbor/trial/multi_step.py:31-51`) loops all steps against the same
  `self.agent_environment`, tearing it down only at the end. `adapter.run()` is
  called once per step (`multi_step.py:104-116`) against that one container.
- So each harness's **on-disk session store persists** (`~/.openclaw`,
  `/root/.hermes/sessions`) — it is simply never resumed. Facts reach a later step
  only via the harness **persistent-memory backend**, never via conversation
  context.

Consequence for the two context tasks:
- `context-management/multistep-context-fill-02` ("compaction under window
  overflow") and `context-rot/context-rot-02` ("in-window lost-in-the-middle")
  both presuppose one accumulating window. There isn't one. **context-rot-02
  cannot test in-window rot at all** — its early/middle/late "rot curve" is keyed
  on *session number*, so any middle-dip is memory-store variance, not attention.

### Structural finding 2 — the memory backend is asymmetric

Post the 2026-06-03 recall-MCP removal the substrate is **openclaw = hindsight-only
vs hermes = honcho + hindsight** (`harnesses/hermes/config.yaml:480-485` +
`harnesses/hermes/honcho.json`). Even a *real* memory gap is uninterpretable while
the two sides carry different memory stores — the same class of confound as the
2026-06-01 provider contamination.

### Per-task findings (all re-verified 2026-06-10)

| # | Task | Verdict | Confirmed fatal issue (file:line) |
|---|---|---|---|
| 1 | memory-conversational-01 | REWORK | 7 short turns fit any window; "Δ0.50" VOID since recall removed; whole-file `no()` greps false-zero precise answers (`steps/07-recall/tests/test.sh:12`) |
| 2 | true-multi-turn-memory-write-01 | REWORK (strongest) | Sound design + real wipe, but whole-file stale-token scan false-zeros honest recaps (`…/tests/test.sh:42-61`); floor risk both-0 if neither harness proactively persists |
| 3 | stale-memory-vs-file-01 | REWORK (≈KILL) | Final prompt names the file and says "**current** value" → one `grep` solves it (`steps/04-query/instruction.md:1`); trap never fires → 1.0/1.0 |
| 4 | context-fill-02 | REWORK | Injected facts are the only 4-space-indented lines → `grep '^    '` pulls them in <1K tokens, window never overflows (`gen_reports.py:143,148`); report body telegraphs "the value that counts is always the LATEST" (`:161-163`) |
| 5 | context-rot-02 | REWORK (KILL-as-redundant) | In-window rot structurally impossible (finding 1); memory-recall test in costume |
| 6 | failure-recovery-loop-01 | **KILL** | `printf '%s' "sk-fetch-9f3a2b71"\|sha256sum\|cut -c1-11` → `8c76e8be959` == expected payload; token literal world-readable (`environment/Dockerfile:78`); `calls=0` scores **max** efficiency (`tests/test.sh:33`) → 1.0/1.0 |
| 7 | tool-sprawl-precision-01 | REWORK (≈KILL) | Answers 19/the/7 computable with plain `python3`/`tr`; correct tool names dead-obvious; no real efficiency dimension → answer-half gameable, caps bypass at 0.5 |
| 8 | plan-then-revise-01 | REWORK (≈KILL) | divide/compose never implemented → revision invalidates no sunk work; `_clamp` sits on disk in `/app/calc.py` at step 3 → "memory" point is a free file-read |
| 9 | sub-agent-parallel-decompose-01 | **KILL** | ~20-line regex reproduced **60/60** answers; parity pre-resolved in prose; concurrency proxy `mtime_burst_peak` not even scored |
| 10 | skill-discovery-and-use-01 | REWORK | Correct skill literally named `csv-structure-summary` matches prompt "structural summary" → name-match, no description-reading forced; no colliding decoys |
| 11 | update-record-with-cleanup-01 | **KILL→REWORK** | Answer-key leak genuinely **fixed** ✓; but it's a one-shot CSV transform and `instruction.md:7-17` enumerates every preservation trap verbatim |

## Scope

**In:**
- Thread multi-step trials into one real conversation (adapter change only).
- Make the memory substrate symmetric: **honcho off, hindsight-only**, for the
  first evidence run.
- Per-task fixes for all 11 (bypass closure, de-telegraphing, grader anchoring).
- Re-earn evidence: strip stale `PROVEN` labels, rebuild image, n≥3 on the new
  substrate.

**Out (deliberately):**
- No Harbor-framework changes — threading is achievable entirely in the two thin
  adapters (the container already persists).
- Not re-enabling recall or honcho for this run (honcho stays a toggle, default
  off; recall stays removed).
- Not promoting any task to `approved=true` until its n≥3 shows a real Δ.

## Design decisions

### D1 — Context pillar: thread steps into one conversation (operator-ratified)

**LANDED 2026-06-10.** Patch `lib/openclaw_thin.py` + `lib/hermes_thin.py` so a task
can OPT IN to threading; when opted in, every step resumes the same harness session
instead of starting fresh. The container persists (finding 1), so the session store
is already on disk; we only pass the resume flag.

- **Flags confirmed in-image** (ran `--help` inside `harbor-agents-rich` on
  <run-host> via ssh, not guessed): openclaw `agent --session-id <id>` (explicit,
  create-or-target); hermes `chat -c/--continue [NAME]` (= most recent session if
  no name). The per-trial container is isolated, so a fixed id / "most recent" is
  unambiguous and `pass^k` repeats can't collide.
- **Opt-IN, not the originally-planned opt-out.** Key realization: since each step
  currently runs FRESH, the memory-recall tasks are *already* memory-dependent
  (facts survive only via the hindsight MCP) — the adversary's "7 turns fit a
  window" critique assumed a threaded conversation that **does not exist** under
  this runner. So threading should be enabled ONLY for the two context tasks;
  memory + single-step tasks keep the fresh-per-step default (correct for them).
  No reset-sentinel needed. Mechanism: a task bakes `/opt/harness/thread-session`
  into its image; the adapters check for it (openclaw → fixed `--session-id
  harbor-trial`; hermes → first step plain, later steps `-c` gated on a
  `/tmp/.harbor_hermes_started` marker). Marker added to context-fill-02's
  Dockerfile.
- **Validated end-to-end (paid smoke on <run-host>, memory ON):** plant a codeword in
  call 1, ask in call 2. openclaw threaded session recalled it; a **fresh-session
  control did NOT** (despite the shared hindsight bank) → recall came from the
  threaded conversation, not memory. hermes `-c` likewise recalled. Both confirmed.
- **context-rot-02 — RE-HOME as a true in-window task (operator 2026-06-10), still
  TODO (T8).** Add the thread-session marker to its image AND restructure so all
  records accumulate in ONE threaded context (its 18 separate "visits" must become
  one growing conversation), then drop the per-session early/middle/late rot-curve
  framing (re-key buckets to real in-context position). The threading mechanism now
  exists; the task-content rework remains.

### D2 — Memory symmetry: honcho off, hindsight-only (operator-ratified)

Honcho has a clean kill switch: `harnesses/hermes/honcho.json` `"enabled"`.
Set it to `false`. hermes then runs hindsight-only (`mcp_servers.hindsight`
remains), matching openclaw. Keep the restore breadcrumb.

- **Rebuild `harbor-agents-rich` after the change** — configs are baked into the
  image, not read live (FOOTGUNS, repeated).
- **Verify by trajectory, not config inspection** — a real hermes run must show
  **zero honcho calls** in the tool catalog/trace. "Disabled in config" ≠
  "not invoked" (same discipline as the provider pin).
- **O1 RESOLVED (operator 2026-06-10): also disable built-in file memory.**
  hermes runs built-in file memory (`MEMORY.md`/`USER.md`, `config.yaml:495-499`)
  that openclaw has no exact match for — leaving it on reintroduces the asymmetry
  honcho-off removed. Set `memory_enabled: false` + `user_profile_enabled: false`.
  **Net substrate for run 1: BOTH harnesses rely purely on the hindsight MCP**
  (`mcp_servers.hindsight`) for cross-step persistence. (Floor risk acknowledged:
  if neither harness proactively writes to hindsight, the memory tasks both score
  0 — an empirical n≥3 question, not a reason to keep the asymmetry.) **Landed.**

### D3 — Bypass closure (the KILL test)

**Hard constraint discovered 2026-06-10: the agent runs as ROOT** (Harbor default,
`harbor/src/harbor/models/task/config.py:221`; no `USER` override; hermes home is
`/root/.hermes`). Therefore **no local secret or local ground-truth is hideable** —
root reads/writes any file in its container, so "root-owned sidecar", "opaque blob
a tool decodes", and "grade against a local expected file" are all forgeable. This
invalidates the original D3 sketch and the existing `failure-recovery` Dockerfile
comment ("airtight fix needs a privilege boundary / stateful sidecar" — a sidecar
does NOT help vs a root agent). Airtight options reduce to: (a) make the agent
non-root — **rejected**, breaks the baked `/root/.hermes` harness home; (b) a
remote secret service dfetch must call — heavy + flaky, rejected for run 1; (c)
**randomize so there is no offline-computable answer, and grade on tool-mediated
side-effects / selection rather than on a reproducible value**, accepting that a
root agent *deliberately* reverse-engineering the grader could still forge, but
honest tool use is the strictly-shorter path so neither harness bypasses in
practice. **Run-1 strategy = (c)** unless operator picks otherwise (decision D3-fork).

- **failure-recovery-loop-01:** replace the deterministic `sha256(token)` payload
  (offline-computable — the live-verified KILL) with a **random nonce generated by
  dfetch at success time**, so the answer is uncomputable from any static file —
  the only way to obtain it is to drive dfetch through the error sequence to
  success. Grade: `payload.txt` must match the nonce dfetch actually emitted
  (recorded in its state) AND a success marker must exist AND calls in the recovery
  band; **no successful call ⇒ 0 (VOID), and `calls==0` must NOT score max
  efficiency** (current bug). Keep the actionable-but-not-spoonfed error strings
  (strip the literal `eu-west|us-east` / token-path giveaways so the loop tests
  diagnosis, not stderr-obedience). Residual root-forgery documented, not hidden.
- **sub-agent-parallel-decompose-01:** kill the fixed prose template (regex
  reproduces 60/60) — heterogeneous structure + a branch that forces real
  computation (state "if odd, add 3" — never assert the outcome). Then calibrate
  N so serial `base<1.0`; score concurrency from trajectory spawn events, not
  mtime bursts. If a single in-context pass still clears it, replace the shape.
- **plan-then-revise-01:** `setup.sh` must strip `_clamp` from `calc.py` and ship
  un-clamped add/multiply, grading the clamp on all three ops (so the policy value
  truly lives only in step-1 conversation under threading); build real sunk work
  the revision invalidates.
- **tool-sprawl-precision-01:** the answer half is gameable and (per the root
  constraint) input-gating won't fix it — a root agent decodes any local blob.
  Instead **drop the reproducible-answer-value half and grade purely on the
  capability we actually want: tool-SELECTION F1 + a real non-clamped efficiency
  dimension.** Computing the value offline then gains nothing because the value
  isn't scored — only which tools were selected and how few calls. Rename the
  correct tools to non-obvious names + add decoys whose names match the task verbs
  better than the answer, so selection requires reading descriptions, not
  name-matching.
- **update-record-with-cleanup-01:** leak is fixed; the remaining job is
  de-telegraphing (D4) + scaling to a stateful workflow (hundreds of rows / many
  months) so trap-handling is discovered, not recited.

### D4 — De-telegraphing (the #1 validity bug)

Remove every line that leaks the eval mechanism:
- update-record `instruction.md:7-17` — delete the enumerated trap list + verbatim
  `55.00/55.10` and `groceries`/`household` examples; give only the user goal.
- context-fill-02 `gen_reports.py:161-163` — drop "the value that counts… is always
  the LATEST one stated"; the agent must infer supersession.
- stale-memory-vs-file-01 `steps/04-query/instruction.md:1` — remove the file path
  and "**current**"; ask a casual recall question so trusting stale memory yields a
  concretely wrong answer.

### D5 — Grader anchoring (kill false-zeros)

Whole-file greps manufacture zeros that look exactly like harness misses. Scope
each precision/stale check to the **labeled answer line** (map question→line, strip
enumerator, pattern-match), not the whole `answer.md`:
- memory-conversational-01 `tests/test.sh` `no()` checks.
- true-multi-turn-memory-write-01 stale-token scan (`:42-61`) + tighten loose
  substrings (`\bcat\b`, `\bmira\b`).
- context-fill-02 — anchor `hit()`/penalties to numbered lines so honest prose
  ("Okafor (was Tanaka)") isn't penalized.

### D6 — Re-earn the evidence

- Strip `PROVEN` from `task.toml`/`configs/core-suite.yaml` for all three anchors
  — Δ0.50 (substrate-void), failure-recovery 1.0-vs-0.0 (bypassable),
  tool-sprawl 3-vs-7 (n=1 anecdote + bypassable). None survive.
- Rebuild `harbor-agents-rich`; **confirm rewardkit is baked into `:latest`**
  (unverified risk — shared-mode reward.py graders silently score 0 if
  `rewardkit` is missing). Run the Harbor **oracle** first (build + schema, no LLM
  cost), then core-suite **n=1** separation, then **n≥3** `pass^k`.
- Reward-kit status (spot-checked clean 2026-06-10): 8/11 core tasks on
  `tests/reward.py` (flat reward.json, leak-free, partial credit). 3 still bespoke
  — failure-recovery (test.sh), plan-then-revise (multistep test.sh), update-record
  (legacy `grade.py`); migrate or document-as-intentional during their rework.

## Acceptance criteria

- [ ] honcho.json `enabled:false`; a real hermes trajectory shows **0 honcho
  calls** post-rebuild.
- [x] Resume flags confirmed from `--help` in-image; both adapters thread; a
  2-step probe shows step-2 sees step-1's conversation (not just memory). DONE
  2026-06-10 (opt-in `/opt/harness/thread-session`; openclaw `--session-id`,
  hermes `-c`; smoke proved threaded-recall with a fresh-session control negative).
- [x] context-fill-02 read-cap truncation FIXED (2026-06-10): reports shrunk to
  ≤1473 lines (build-time `assert` on `MAX_LINES_PER_FILE=1700`) so a ~2000-line
  read cap can't drop section-7/8 facts into false zeros; latest-section fact now
  at line ~1308; cumulative ~728K tokens (above the ~300-400K knee); grep-immunity
  intact. Still [ ]: does it OVERFLOW on the intended path (re-confirm post-threading).
- [ ] context-rot-02 re-homed or KILLed (no false "rot curve") — blocked on threading.
- [ ] All 5 bypasses closed — re-run each exploit and confirm it no longer scores.
- [ ] Telegraphing lines removed (D4); graders anchored to labeled lines (D5) —
  a correct *disambiguating* answer no longer scores 0.
- [ ] `PROVEN` labels removed; oracle green; core-suite n=1 separates; n≥3 shows a
  real Δ (not 1.0/1.0 or 0/0) before any `approved=true`.

## Run log (2026-06-10)

- **Rich image rebuilt** with honcho-off + file-memory-off; verified baked
  (`honcho.json "enabled": false` in-image). rewardkit confirmed present.
- **Oracle (free, all 11): 11/11 at mean 1.000** — every reworked task builds, its
  `solution/solve.sh` runs, and its grader accepts it (incl. the separate-verifier
  skill-discovery task and both threaded context tasks). Structural validity green.
- **n=1 separation run (real harnesses): SUITE DISCRIMINATES.** Effective overall
  Δ = 0.136 (MEETS the 10% bar), leader hermes. Reliability split too: openclaw 9%
  error (1 timeout on a threaded context task) vs hermes 0%. Per-category:
  - skill-agent-authoring oc 0.50 / he 1.00 (Δ−0.50) — strong
  - context-management   oc 0.25 / he 0.75 (Δ−0.50) — strong; **threading live**
    (hermes 175M vs openclaw 20M tokens on the context task = real accumulation)
  - conversation-persona oc 0.67 / he 0.50 (Δ+0.17)
  - ops-debugging        oc 0.93 / he 1.00 (Δ−0.07)
  - tool-orchestration   oc 0.50 / he 0.50 (Δ0) — flat (watch at n=5)
  - real-world-workflows oc 0.56 / he 0.56 (Δ0) — flat but well off 1.0 (hard, not saturated)
  - context-rot          oc 1.00 / he 1.00 (Δ0) — **SATURATED**; multi-hop too easy
    even threaded → needs harder chains regardless of n (follow-up).
- **n=5 `pass^k` grid (110 trials) — DONE. The suite is a strong discriminator.**
  Overall effective Δ = **0.188** (MEETS bar), leader **hermes**. Reliability is
  itself a major signal: **openclaw 20% error (9% crash, 11% timeout), raw 0.485 →
  eff 0.445; hermes 4% error, raw 0.654 → eff 0.632.** **ALL 7 categories split
  ≥10%, in BOTH directions** (not a one-sided artifact):
  - conversation-persona  oc 0.10 / he 0.63  Δ−0.53
  - skill-agent-authoring oc 0.60 / he 0.95  Δ−0.35
  - ops-debugging         oc 0.93 / he 0.60  Δ+0.33  (openclaw wins — failure-recovery)
  - real-world-workflows  oc 0.62 / he 0.82  Δ−0.20  (split emerged at n=5; flat at n=1)
  - tool-orchestration    oc 0.49 / he 0.34  Δ+0.15  (openclaw wins; flat at n=1)
  - context-management    oc 0.15 / he 0.30  Δ−0.15  (both low — hard; hermes manages overflow better)
  - context-rot           oc 0.90 / he 1.00  Δ−0.10  (was 1.0/1.0 saturated at n=1; openclaw variance opened a thin split — still the weakest, candidate for harder chains)
  - **conversation-persona FLIPPED sign vs n=1** (oc +0.17 → he −0.53), confirming
    n=1 is a coin-toss and n≥3 reliability is the real signal — exactly the
    methodology's point. **Verdict: the reworked suite detects a real harness gap on
    the identical model; the thesis precondition is met.**

## Open questions

- ~~**O1 (D2):** neutralize built-in file memory too?~~ **RESOLVED** — yes,
  disabled for run 1; hindsight-only both sides. (landed)
- **O2 (D1):** stable session-id scheme — derive from Harbor trial id (is it
  exposed to the adapter via `AgentContext`?) or mint one in step 1 and stash it
  in a known container path the next step reads.
- **O3:** does `configs/core-suite.yaml`'s `path:` (`<repo>/…`,
  the pre-move <dev-host> path) still resolve on <run-host>, or does it need updating to
  `~/benchmarking/harbor-tasks`? Verify before the run.

## Follow-up tickets

- Per-task rework specs may be split out if any single fix (sub-agent redesign,
  context-rot re-home) grows beyond a paragraph.
