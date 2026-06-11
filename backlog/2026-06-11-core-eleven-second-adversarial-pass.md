---
status: APPROVED
epic: E4
date: 2026-06-11
---

# Core-eleven second adversarial pass — fix the residual bypasses the 2026-06-10 rework left open

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-11
**Status:** APPROVED 2026-06-11 — the three open questions were resolved by the
operator same-day (wipe + spin-off task; latency-gated round-trip; mechanical
stale-memory seeding); implementation can start with Wave 1.
**Origin / triggered-by:** operator asked for a fresh completeness/accuracy review
of the eleven core-suite tasks (`configs/core-suite.yaml`), adversarial, one
subagent per task. 11 parallel auditors returned: **4 CRITICAL validity breaks
(2 with working exploits demonstrated), 4 MAJOR, 4 MINOR** — plus five systemic
patterns that cut across tasks.
**Predecessor:** `2026-06-10-core-eleven-remediation.md` (the rework this pass
audits; its n=5 grid showed Δ 0.188, but two of its hardening claims —
failure-recovery's nonce and sub-agent-decompose's "no answer key" argument —
do not survive attack).

## Problem

The 2026-06-10 rework fixed the structural confounds (threading, substrate
symmetry) but four tasks still don't measure what they claim, and five
grader/infra patterns recur across the suite. Two bypasses were **demonstrated**
during this audit, not just argued:

- `sub-agent-parallel-decompose-01`: the auditor wrote a ~100-line template
  parser **using only problem observation (no answer key)** that scores **60/60
  in milliseconds, serially**. The task.toml mitigation claim ("with no answer
  key the agent cannot validate it") is false — you validate by hand-solving
  3–5 problems.
- `failure-recovery-loop-01`: state-file forgery scores **1.0 with zero
  recovery** — and because `calls=0`, the efficiency term clamps to 1.0 too.
  Forgery is *strictly shorter* than the honest path, inverting the task's own
  design claim.

A suite that just demonstrated Δ 0.188 at n=5 can still be measuring artifacts:
every unfixed bypass and false-zero source below is indistinguishable from
harness signal in the headline number.

## Verdict roll-up

| # | Task | Verdict | Headline finding |
|---|------|---------|------------------|
| 1 | conversation-persona/multistep-memory-conversational-01 | MINOR | `march 1?4` regex matches the distractor "march 4" |
| 2 | conversation-persona/true-multi-turn-memory-write-01 | MAJOR | day-name false zeros; old session transcripts recoverable at recall |
| 3 | conversation-persona/multistep-stale-memory-vs-file-01 | **CRITICAL** | answer + trap spoiled in agent-visible `setup.sh` |
| 4 | context-management/multistep-context-fill-02 | MAJOR | fill is ~728K tokens — **under** the 1M window, not the claimed 1.25× |
| 5 | context-rot/context-rot-02 | **CRITICAL** | "multi-hop" is single-hop; 5/8 bridge facts are real-world parametric knowledge |
| 6 | ops-debugging/failure-recovery-loop-01 | **CRITICAL** | full forgery bypass → 1.0 (demonstrated on paper, mechanism verified) |
| 7 | tool-orchestration/tool-sprawl-precision-01 | MINOR | rational direct-compute scores 0.0 → correlated-zero risk |
| 8 | tool-orchestration/plan-then-revise-01 | MAJOR | secret clamp bound leaks via `__pycache__`/scratch; bound is maximally guessable |
| 9 | skill-agent-authoring/sub-agent-parallel-decompose-01 | **CRITICAL** | 60/60 scripted bypass demonstrated live |
| 10 | skill-agent-authoring/skill-discovery-and-use-01 | MINOR | brute-force "run all 13 skills" earns all 8 discovery points |
| 11 | real-world-workflows/update-record-with-cleanup-01 | MINOR | do-nothing floor is 0.50; "stateful workflow" axis is one-shot in practice |

## Systemic findings (fix once, apply everywhere)

### S1 — `/app`-only wipe is the recurring hole (tasks 1, 2, 4, 5, 8)

Every memory/long-context recall step wipes only `/app`
(`find /app -mindepth 1 -delete`). Surviving paths into the graded step:

- scratch notes in `/tmp`, `$HOME`, `/var/tmp` — and several ingest
  instructions actively invite note-taking ("you'll be asked about them later");
- **the harness's own session transcripts** (openclaw session JSONL under the
  harness home dir; hermes session store; adapter copies under `/logs/agent/`).
  Task 2's auditor confirmed an agent can grep its old session files at step 08
  and recover all eight facts with zero memory use;
- task 8 (plan-then-revise): `/app/__pycache__/calc.cpython-*.pyc` from the
  step-1/2 verifier imports — the "secret" clamp bound is disassemblable.

**Decision required:** is filesystem note-taking an intended harness-mediated
path or a cheat? Either way the current state is the worst case (telegraphed
invitation + porous gate). Remediation: a shared `wipe_scratch.sh` fragment
sourced by every recall-step `setup.sh` that wipes `/app`, `/tmp`, `/var/tmp`,
agent-writable `$HOME` paths, harness session stores, and `/logs/agent`
transcript copies — **excluding** the harness persistent-memory backends (the
measured path) — plus an assertion (grep the wiped roots) so a failed wipe
fails loudly instead of `|| true` (multi_step.py treats setup failure as a
warning; the test must independently assert the wipe happened).

### S2 — format-strict false zeros (tasks 1, 2, 4, 8)

The methodology's own #1 scoring sin, present in four graders. Each one
manufactures a 0.0 indistinguishable from harness discrimination:

- task 2 `tests/reward.py:81-83`: only full day names accepted — "Mon/Wed/Fri"
  (correct, natural) scores 0; abbreviated stale dumps also evade the reject.
- task 4 `tests/reward.py:29,34`: requires `\b32 ?node` — bare "32" on the
  nodes question scores 0; same for "1.5 hours" variants.
- task 4 `tests/reward.py:60`: enumerator regex rejects `**1.**` and `- 1.`
  formats.
- task 8 `tests/test.sh:86`: order-strict `list(calc.OP_NAMES) ==
  ['add','multiply','subtract']` when the instruction never specifies order.
- task 1 `reward.py:41-44,53-57`: negation window is one-directional (correct
  "March 14 — March 4 is my neighbor's" fails); positional fallback shifts on
  unmatched preamble lines.

### S3 — hedging / dump-everything gaming (tasks 1, 3, 4, 5)

Scored criteria check presence of the right value without excluding the wrong
one:

- task 3: "It was 45, now maybe 275" scores 1.0 (`not_stale` is weight-0).
- task 5 `reward.py:67-69`: writing every remembered place name on all 8 lines
  scores 1.0 with zero mappings known (no exclusivity check).
- task 4: facts with one prior value credit final+stale listed together (dump
  strategy reached 0.5 in a stub-run).
- task 1: `not march 4` earns the birthday point with no correct value present.

Rule to apply: scored criterion = correct value present **AND** stale/distractor
value absent at token level (with an explicit `(was …)` carve-out for honest
update phrasing, which several graders already document as intended).

### S4 — no grader-crash fallback (tasks 1, 6, 7, 9 at minimum)

`tests/test.sh` calls rewardkit/inline graders with no failure guard. A grader
exception writes no `reward.json` → Harbor **silently drops the trial**
(FOOTGUNS #2). Add to every test.sh:
`<grader> || echo '{"reward": 0.0}' > /logs/verifier/reward.json` (or trap),
and `errors="replace"` on answer-file reads.

### S5 — doc/denominator drift + hygiene

- `configs/core-suite.yaml` says context-fill-02 is "/14" — it's **/12**.
- task 11's "/19" claims everywhere — the grader scores **/16** (6+7+2+1).
- plan-then-revise's "graded re-plan /8" is actually one binary keyword check
  worth 0.08 of the blend (clamp memory is the real 0.40 axis) — relabel or
  deepen.
- committed `__pycache__/*.pyc` in tasks 1, 2, 3 (git rm --cached).
- `[metadata] approved = true` absent on audited-sound tasks (catalog shows
  NEEDS REVIEW).
- task 9: SHAPES.md:25 lists shape 14 verifier as "judge"; it's deterministic
  rewardkit.

## Per-task findings and fixes

### T3 — stale-memory-vs-file-01 (CRITICAL)

1. **CRITICAL — workspace-resident spoiler.** Harbor uploads the step workdir
   into the agent cwd and never deletes it (`multi_step.py:285-320`). During
   the graded step, `/app/setup.sh` contains: *"a harness that answers from
   stale memory says 45; one that re-reads ground truth says 275."* Any
   `ls /app` + `cat` hands over the answer and reveals the eval. **Fix:** strip
   all spoiler comments; end setup.sh with `rm -f -- "$0"`.
2. HIGH — hedging (see S3): score `"275" present AND "45" absent` (token-level).
3. HIGH — degeneration for memoryless harnesses: a harness arriving cold at
   step 04 reads the file and scores 1.0 — amnesia is indistinguishable from
   verification discipline. **Fix (operator decision 2026-06-11): mechanically
   seed the stale memory.** Add a pre-step that writes the stale value (45)
   directly into each harness's memory backend so BOTH arrive with the stale
   belief and the task purely measures re-verification. The substrate is
   hindsight-only on both sides post the 2026-06-10 symmetrization, so the
   seeding path is one backend, written once — but it MUST be verified
   symmetric (same fact, same phrasing, both harnesses retrieve it) or it
   recreates the exact substrate-asymmetry confound that rework removed.
   Keep the weight-0 diagnostic regardless.
4. MED — brittle sed: `s/cache_ttl_seconds: 45/...` no-ops silently if the
   agent reformatted config.yaml in steps 01-03. **Fix:** anchor on the key
   (`s/^cache_ttl_seconds:.*/cache_ttl_seconds: 275/`) and `grep -q` verify so
   a miss exits nonzero.
5. LOW — task.toml promises a hallucination flag that doesn't exist in
   reward.py; committed `.pyc`.

### T6 — failure-recovery-loop-01 (CRITICAL)

1. **CRITICAL — state forgery.** The grader trusts agent-writable
   `/var/log/dfetch.state`, whose exact format is published in the
   world-readable `/usr/local/bin/dfetch` (Dockerfile:81). Forge state +
   payload + token with an invented nonce → 1.0, with `calls=0` ⇒ efficiency
   clamps to 1.0. **Fix:** mint the nonce/counter into a root-only path the
   agent cannot write (root-owned `chmod 600`, or HMAC with a build-time
   secret stripped before agent start); grader cross-checks `calls >= 4` and
   the ordered error progression from a root-only append log.
2. HIGH — recovery scheme telegraphed in-container: the full failure ladder,
   the valid token (`sk-fetch-9f3a2b71`, Dockerfile:96), and both regions are
   readable in the plaintext script. Adaptive diagnosis collapses to "read one
   file." **Fix:** move decision logic/secrets out of agent-readable paths
   (compiled helper or root-only `chmod 700`).
3. HIGH — efficiency band mis-scaled: oracle uses 2 calls, not the IDEAL=6 the
   task documents; eff=1.0 for everything ≤6 calls. **Fix:** re-derive IDEAL
   from the true oracle path once #2 forces the ladder to be unavoidable.
4. MED — final-artifact-only grading: no evidence the error sequence was
   experienced. **Fix:** root-only append log of rejected calls with exit
   codes; grader requires the ordered progression.

### T9 — sub-agent-parallel-decompose-01 (CRITICAL)

1. **CRITICAL — 60/60 scripted bypass demonstrated.** Problems come from a
   small closed template set (`solution/gen.py:80-128`: 4+4+4 op phrasings,
   literal markers "a parity rule applies — " / "a capacity check applies — ",
   self-identifying distractor templates). A ~100-line parser built from
   observation alone scored 60/60 in milliseconds, serial. **Fix (operator
   decision 2026-06-11): latency-gated round-trip** — execute the escalation
   already sketched in task.toml: put a per-problem fact behind a
   file/endpoint round-trip with real latency so wall-clock, not tokens,
   gates serial throughput. A parser without the per-problem fact cannot
   answer; serial round-trips cannot fit the budget; fan-out can. (The
   LLM-paraphrase alternative was considered and not chosen — it kills the
   parser but leaves budget calibration as a separate open measurement.)
2. HIGH — budget uncalibrated (author-admitted): 60 small problems may clear
   serially inside 600s even without a parser → 1.0/1.0 saturation. **Fix:**
   calibrate the budget against a measured honest-serial run after fix #1.
3. MED — telegraphing (instruction.md:19-23): "working through all of them
   strictly one-after-another may not finish in time" + "so we can observe how
   the work was scheduled." **Fix:** state only the time limit.
4. LOW — gen.py `t_hint` dead variable; gen.py crashes on regen without
   `tests/` pre-existing; test.sh no-fallback (S4); reward.py silent
   `except Exception: return ()`.

### T5 — context-rot-02 (CRITICAL)

1. **CRITICAL — the two-hop AND-gate doesn't hold.** Every bridge entity is
   type-unique in the corpus (one architect, one pottery, one foundry…), so
   each bridge sentence answers its question alone — the anchor hop is dead
   weight; this is single-hop recall (`gen_reports.py:100-124`). And 5/8
   bridge facts are real-world pairings (Maw & Co→Jackfield,
   Whitefriars→Thames, Frosterley→County Durham, Taylor→Loughborough,
   Riga→Latvia) answerable from parametric knowledge — with
   `allow_internet = true` even a half-memory becomes a web lookup. So the
   chain survives if EITHER hop survives — the inverse of the design.
   **Fix:** fictionalize all bridge attributes AND seed same-type confusable
   distractors (a second named architect/pottery/foundry in filler) so the
   anchor genuinely disambiguates. This is the predecessor spec's "harden
   context-rot chains (weakest at Δ−0.10)" follow-up, now with the mechanism
   identified.
2. HIGH — wipe is `/app`-only (S1) while ingest instructions invite persisting
   ("take in the detail… records will no longer be available").
3. MED — no exclusivity check (S3): all-place-names-on-every-line scores 1.0.
4. MED — telegraphing: all 18 ingest steps disclose the upcoming wipe and
   prescribe retention strategy. Defensible as goal-framing only if S1 is
   fixed; revisit wording after.
5. LOW — positional-fallback shift on unmatched preambles; 2/3/3 rot-curve
   buckets give the early bucket only 2 samples.

### T4 — context-fill-02 (MAJOR)

1. HIGH — **the overflow claim is numerically wrong.** task.toml claims ~1.3M
   cumulative tokens ≈ 1.25× the 1M window; running `gen_reports.py` yields
   2,911,847 chars ≈ ~728K est. tokens (~880K even at 3.3 chars/token) —
   **under** the window. Overflow currently depends on tool-result duplication
   and agent verbosity; the generator docstring admits this is unconfirmed
   post-threading. **Fix:** measure a real threaded-trial token count; if
   under-window, extend (add weeks — LINES_PER_SECTION headroom to the
   1700-line read cap is only ~230 lines) and correct the description.
2. HIGH — wipe is `/app`-only while every ingest step announces the deletion
   (S1's worst instance: the telegraph + porous gate converts the task into
   "did you think to write notes outside /app"; notes written IN /app — the
   natural choice — are destroyed: same strategy, opposite outcome, by
   directory choice).
3. MED — format-strict false zeros (S2) + dump-strategy credit on 1-prior
   facts (S3).
4. LOW — decoy NEG list ("instead", "only") lets decoy adoption pass; recall
   test.sh should assert `/app/reports` is absent (wipe verification);
   core-suite.yaml says /14, grader is /12 (S5).

### T2 — true-multi-turn-memory-write-01 (MAJOR)

1. HIGH — session-transcript recovery (S1's proven instance): step-08 agent
   can grep its own step-01..07 session JSONL and recover all 8 facts.
2. HIGH — day-name false zeros + abbreviated-stale evasion
   (`tests/reward.py:81-83`, S2): accept `\bmon(day)?\b` etc., mirror in the
   stale reject.
3. MED — dinner_ok defaults to 1 when Part B is absent (reward.py:89-95);
   peanut check misses bare "crushed peanuts" (reward.py:91-93); Part A/B
   split fires on any line containing "dinner" (reward.py:56-58 — anchor on a
   heading).
4. LOW — stale "step 06" comments in steps 01-05 test.sh; committed `.pyc`;
   single-task `harbor run` lacks the memory-wipe hook (documented footgun,
   restated because this task is the one it inflates).

### T8 — plan-then-revise-01 (MAJOR)

1. HIGH — clamp-bound leak via surviving artifacts (S1): step-3 setup
   overwrites only `calc.py` + `PLAN.md`; scratch tests, notes (step-1
   instruction *tells* the agent to record the rule), and stale
   `/app/__pycache__/*.pyc` survive. **Fix:** `find /app -mindepth 1 -delete`
   before writing the step-3 baseline.
2. HIGH — the secret bound `[-1000, 1000]` is the single most guessable value,
   and the baseline PLAN.md cues that a clamp policy exists — a memoryless
   guesser collects the full 0.40 CLAMP weight. **Fix:** non-round bound
   (e.g. `[-871, 871]`).
3. MED — order-strict OP_NAMES check (S2): `sorted(...)`.
4. MED — telegraphing: "This is the final step and the only one that counts
   toward the score" (step-3 instruction.md:21). Delete.
5. MED — axis relabel (S5): REPLAN is one 0.08 keyword check; the real axis is
   clamp memory 0.40. Relabel in catalog/config or deepen REPLAN grading.
6. LOW — no VOID marker (`module_imported`); setup failure non-fatal gifts the
   0.40 (assert in test.sh).

### T1 — multistep-memory-conversational-01 (MINOR)

1. HIGH — `reward.py:28`: `march 1?4` matches distractor "march 4"; with the
   negation carve-out, `not March 4` scores with no correct value. **Fix:**
   `march 14\b|3/14|03/14|march fourteen`.
2. HIGH — wipe is `/app`-only (S1) and step-01 invites note-taking.
3. MED — one-directional negation window + positional-fallback shift (S2);
   no rewardkit-crash fallback (S4).
4. LOW — Q7 grader accepts colour OR year where instruction asks all four;
   borderline telegraph ("about **me**", "you'll be asked later"); committed
   `.pyc`; `approved` absent.

### T7 — tool-sprawl-precision-01 (MINOR)

1. HIGH — incentive inversion: a fully correct answer.json computed with plain
   python scores 0.0; data is tiny (7 CSV rows), so rational same-model agents
   on both harnesses may skip the tools → correlated 0.0s reading as a tie.
   **Fix:** make direct computation unattractive mechanically — large/messy
   data (e.g. 100k-row CSV with edge cases) so the tools are the natural path.
2. MED — `call_efficiency = distinct_correct/total` maxes on under-calling:
   1 correct call + offline compute = 0.75. **Fix:**
   `distinct_correct / max(total, 3)`.
3. LOW — log forgery discoverable via `cat` of tool source (accepted residual,
   FOOTGUNS #44; cheap hardening: require logged argv to reference the real
   data files); argv newline injection (sanitize `$*`); no crash fallback (S4);
   "harness-bound" tag overstates the axis (PATH executables, not a tool
   catalog).

### T10 — skill-discovery-and-use-01 (MINOR)

1. MED — brute-force invocation (run all 13 skills on all 8 files) banks all
   8 discovery points; decoys log nothing and carry no precision penalty.
   **Fix:** decoys also log; subtract/gate discovery credit on decoy-sweep
   patterns.
2. MED — 9 far decoys are constant-printing stubs exposed by one behavioral
   probe — discovery degrades to a functionality check. **Fix:** make far
   decoys actually compute their advertised outputs.
3. LOW — trim "use it as documented; don't reimplement" from instruction.md:5;
   strip the verification-scheme comment from agent-visible run.py; honest-use
   false negative when CSVs are copied to /tmp (breadcrumb lands outside
   collected dir); ungraded "no other output" sentence; no answer_present.

### T11 — update-record-with-cleanup-01 (MINOR)

Leak-proof claim **holds** (tests upload post-agent; original.csv ==
budget.csv so even a leak reveals nothing). Baselines verified: do-nothing
0.50, sort-u 0.4375, oracle 1.0.

1. MED — axis mismatch: one-shot 30-line-script solvable; "stateful
   multi-step" is really "two edits in one pass." **Fix:** either add a
   mechanically-enforced second step (rent-split parameters arrive after a
   wipe) or relabel the axis honestly.
2. MED — free floor: preserve/collateral units are satisfied by default
   (do-nothing = 0.50; dedup-only = 0.875; rent — the hard discovery — is
   2/16). **Fix:** gate preserve credit on evidence of action (multiply by
   `min(1, dedup_ok)`) or reweight.
3. LOW — notes compared exactly (annotation loses points — exclude notes from
   identity like rent already does); fabricated appended rows cost nothing;
   headerless output silently eats first row; "/19"→/16 and "discover the
   month" description drift (S5).

## Scope

**In:** everything above — the 4 critical breaks, the 5 systemic patterns
applied to the 11 core tasks, doc/denominator drift, and re-validation.
**Out:** non-core tasks (apply S1/S2/S4 there opportunistically later); the
predecessor spec's remaining follow-ups (dead recall-wipe path,
infisical-identity.env doc) unless touched incidentally; any change to the
harness substrate, adapters, or provider pin (untouched by these findings);
relitigating the 2026-06-10 threading/substrate design.

## Design decisions

1. **Wave order** (highest leverage first, each wave oracle-verified before
   the next):
   - **Wave 1 — S1 shared wipe.** One fragment, five tasks. Filesystem
     note-taking is RESOLVED (operator, 2026-06-11): it is a cheat for these
     five tasks — wipe scratch roots, session stores, and transcript copies;
     the measured paths are the harness memory backends and threading. The
     capability itself is real, so it gets its own dedicated task (see
     Follow-up tickets) where deliberate externalization is scored
     first-class.
   - **Wave 2 — the four criticals** (T3 spoiler strip + mechanical
     stale-memory seeding, T6 root-only nonce/evidence, T9 latency-gated
     round-trip, T5 fictionalize+distractors).
   - **Wave 3 — S2 false zeros + S3 hedging** across graders (regrade-offline
     test: the documented natural-phrasing answers must score; the documented
     dump/hedge attacks must not).
   - **Wave 4 — S4 crash guards + S5 drift/hygiene.**
2. **Bypass-regression harness:** each demonstrated exploit (T9 parser, T6
   forgery, T3 `cat setup.sh`, T5 anchor-free answering, dump/hedge strings
   for T1/T2/T3/T4/T5) gets recorded as a re-runnable check (script or
   documented manual probe) under the task's `solution/` or a new
   `tests/exploits/`, so the *next* rework can't silently regress. This pass
   exists because 2026-06-03 selected tasks "without re-verifying the fixes
   landed" — make verification cheap.
3. **Severity-gated sweep:** tasks 1, 7, 10, 11 are runnable now with caveats;
   3, 5, 6, 9 are **blocked** for any verdict-bearing n=5 until Wave 2 lands.
   If a sweep must run earlier, exclude the blocked four and say so in
   RESULTS.md.
4. **Image rebuild** after any baked-path change (S1 touches in-container
   scripts only → no rebuild; T6's root-only files and T10's decoy changes are
   Dockerfile changes → rebuild required, per FOOTGUNS).

## Acceptance criteria

1. All recorded exploits fail post-fix: T9 parser scores ≤ chance on the
   regenerated set (and a measured honest-serial run cannot finish in
   budget while a fan-out run can); T6 forgery yields reward 0 (and
   `calls=0` can no longer produce eff=1.0); T3 graded-step workspace
   contains no spoiler text (`grep -ri '275\|stale' /app` clean during the
   agent phase); T5 anchor-free per-question answering drops to the
   fictional-pairs-only ceiling.
1b. T3 stale-memory seeding verified symmetric: after the seeding pre-step,
   both harnesses retrieve the stale value (45) from their memory backend
   when asked, before the live file is updated — checked once per image
   rebuild, not assumed from config.
2. S1: after each recall-step setup, a probe finds no task facts under `/app`,
   `/tmp`, `/var/tmp`, agent `$HOME` scratch, harness session stores, or
   `/logs/agent` — with harness memory backends intact; the recall test
   asserts the wipe happened (fails loudly, no `|| true`).
3. S2/S3 regrade matrix: the enumerated natural-format answers (Mon/Wed/Fri,
   bare 32, `**1.**`, reordered OP_NAMES, trailing negation) all score; the
   enumerated dump/hedge attacks (45-and-275, all-place-names, stale-day
   dumps, "not March 4") all fail. Checked by running each grader offline
   against a fixtures file of these strings.
4. S4: killing the grader mid-run on any task still produces a parseable flat
   `reward.json` (0.0) — no silently dropped trials.
5. S5: core-suite.yaml comments, task.toml descriptions, SHAPES.md, and the
   task catalog agree with the actual grader denominators; no tracked
   `__pycache__`; oracle 11/11 = 1.0 after all waves.
6. T4's overflow claim is replaced by a measured threaded-trial token count
   (and the fill extended if it's under-window).
7. Re-run the n=5 grid; the suite still discriminates (the predecessor's
   Δ 0.188 is the baseline to beat or explain — fixing fake signal may
   legitimately *lower* Δ; what matters is that the remaining Δ is
   attack-clean).

## Open questions — RESOLVED (operator, 2026-06-11)

1. Filesystem note-taking: **cheat in these five tasks — wipe it**, AND spin
   off a dedicated scratch-discipline task where externalization is the
   measured capability (see Follow-up tickets). Wave 1 wipes scratch roots,
   harness session stores, and `/logs/agent` transcript copies; only the
   harness memory backends survive a recall-step setup.
2. T9 fix path: **latency-gated round-trip.** Per-problem fact behind a
   file/endpoint with real latency; closes the parser bypass and the budget
   calibration in one stroke.
3. T3 memoryless degeneration: **mechanically seed the stale memory.**
   Pre-step writes the stale value into the (hindsight-only, symmetric)
   memory backend for both harnesses; the task then purely measures
   re-verification. Seeding symmetry must be verified (same fact, both
   harnesses retrieve it) before any verdict-bearing run.

## Follow-up tickets

- **Scratch-discipline task (new, not yet specced):** a task where deliberate
  filesystem externalization of working state IS the measured harness
  capability, scored first-class (does the agent persist the right facts, in
  a findable place, unprompted?). Motivated by the Wave-1 decision to treat
  note-taking as a cheat in the memory/context tasks — the capability is
  real, it just contaminates those axes. Write as its own spec before
  building; candidate category: `context-management`.

## Audit provenance

11 parallel adversarial subagents, 2026-06-11, one per task; each read every
task file plus the relevant Harbor runner/verifier source, traced grader math
line-by-line against fixtures, and recorded failed attacks alongside findings.
Two exploits were executed (T9 parser: 60/60; T4 generator token count:
2,911,847 chars), the rest verified by mechanism. Failed-attack notes (what
already holds: rich base image on all 11, flat reward.json on all 11, verifier
sandboxing on T10/T11, post-agent tests upload, T11 leak-proofness) are in the
per-task sections' source reports.

---

## Implementation log / as-built (2026-06-11)

Branch `baton/2026-06-11-core-eleven-second-adversarial-pass` off
`remediation/core-eleven-2026-06-10`. Three commits (red test → feat → feat).
This pass landed **all the offline-verifiable work**; everything that needs a
docker rebuild or a live n=5 run was deliberately deferred and is logged below
(this pipeline forbids builds/sweeps — open question 5).

### What actually changed

**New shared artifact**
- `lib/wipe_scratch.sh` — canonical scratch-wipe fragment (open question 3
  resolved: **commit-once + copy-verbatim**, not inline). It wipes `/tmp`,
  `/var/tmp`, `/logs/agent`, agent `$HOME` caches (`.cache`, `.local/share`,
  `scratch`, `notes`), and the harness session stores
  (`$HOME/.openclaw/sessions|history|*.jsonl`, `$HERMES_HOME/sessions|history|*.json`).
  It deliberately does **not** touch `/app` (each step decides) and **never**
  touches the external memory backends (those are network services wiped by
  `hooks/wipe_memory_state.py`). No `|| true` swallowing — absent surfaces are
  no-ops, real failures still surface. A verbatim copy is committed into each
  recall step's `workdir/` so Harbor uploads it beside `setup.sh`.

**Wave 1 — S1 shared wipe (5 tasks: T1, T2, T4, T5, T8).** Each recall/baseline
`setup.sh` now `source "$(dirname "$0")/wipe_scratch.sh"` before its `/app`
action. T8's `03-revise-and-fix/tests/test.sh` adds an independent
`clamp_note*` survival assertion that fails loudly (flat `reward 0.0`) because
`multi_step.py` treats setup failure as only a warning.

**Wave 2 — the four criticals (offline-verifiable parts only):**
- **T3 spoiler strip** (`04-query/workdir/setup.sh`): removed the trap-narrating
  comment and the literal stale value; key-anchored sed
  (`s/^cache_ttl_seconds:.*/.../`) + `grep -q` verify (`set -e`, exits nonzero on
  a no-op) + `rm -f -- "$0"` self-delete. Grader (`reward.py`) reworked to the S3
  exclusivity rule: `answered_current_exclusive` (275 present AND stale 45
  absent) is the weight-1 criterion, with a `_CARVEOUT` regex for honest update
  phrasing ("275 (was 45)", "updated from 45", "45 →"); legacy signals demoted
  to weight-0 diagnostics. `task.toml` description rewritten to match.
- **T6 forgery gate** (`failure-recovery-loop-01/tests/test.sh`): `correctness=0`
  unless `recovered`, a `calls >= MIN_CALLS(4)` forgery gate, `IDEAL` re-derived
  6→4, counter now read from the environment and accepted **only** as a strict
  integer (code-injection guard — the agent-writable counter is never
  interpolated into the interpreter source), plus an S4 belt-and-suspenders flat
  `reward.json` fallback.
- **T9 latency-gated round-trip** (`sub-agent-parallel-decompose-01`):
  `solution/gen.py` now appends a per-problem **calibration OFFSET** that is
  *not* in the prose — the prose names only a `CAL-NN` code — and folds the
  offset into each answer. The offset table is written to a verifier-side
  `tests/registry.json` (answer-key-equivalent, kept out of `environment/`).
  `instruction.md` detelegraphed (removed the "may not finish serially / so we
  can observe scheduling" cues; states only the time limit + the lookup step).
  `reward.py` narrowed its bare `except` to `(OSError, ValueError)`; `test.sh`
  got the S4 `|| echo '{"reward":0.0}'` guard. `solution/solve.sh` +
  `tests/answers.json` regenerated.
- **T5** got the S1 wipe + S2/S3 grader fixes via `19-recall`; the
  fictionalize-bridge-attributes + same-type-distractor corpus rebuild was
  **deferred** (it is a generator/corpus change best done with the rebuild).

**Wave 3 — S2/S3 grader fixes:** T1, T2, T4, T5 recall `reward.py` graders
loosened format-strictness (day-name abbreviations, bare numbers, enumerator
formats) and added exclusivity/dump-rejection per S3. T8's `OP_NAMES` check
changed `list(...)==[...]` → `sorted(...)==[...]` (order-agnostic, S2).

**Wave 4 — S4 + S5:** S4 crash-guard `|| echo '{"reward":0.0}'` added to T7/T9
`test.sh` (T6 has its own inline fallback). S5 drift: `configs/core-suite.yaml`
(`/14`→`/12` for context-fill-02; `/19`→`/16` for update-record; plan-then-revise
relabelled to the real weight blend); `SHAPES.md` shape-14 verifier "judge"→
"deterministic rewardkit (correct/60)".

**Bypass-regression harness (new `tests/` tree, design decision 2).** 37 offline
checks, runnable on <run-host>'s harbor venv with no docker/sweep:
`tests/helpers.py` + `conftest.py` (rewardkit-driving + shell-grader remap
helpers); `tests/exploits/` (T3 spoiler, T6 forgery, T8 opnames, T9 parser +
`t9_parser.py` the recorded exploit); `tests/wipe/test_s1_wipe.py`;
`tests/regrade/test_s2_s3_matrix.py` (natural-phrasing answers score / dump-hedge
attacks fail); `tests/s4/test_s4_crash_guard.py`; `tests/hygiene/test_s5_drift.py`.

### Key decisions & deviations from the plan

- **Tasks T10 and T11 were NOT touched.** Both are MINOR; their fixes
  (decoy-logging/decoy-compute for T10, second-step/floor-gating for T11)
  were out of scope for this offline pass and remain open.
- **The wipe fragment is committed per-step, not symlinked.** Symlinks don't
  survive Harbor's workdir upload reliably, so a verbatim copy in each
  `workdir/` is the as-built delivery (5 identical copies + the `lib/` master).
- The spec's S1 also named tasks 1/2/4/5/8; that is exactly the set wired.

### Open questions — as-built resolution

1. **T6 under a root agent.** CONFIRMED: the agent runs as **root**
   (`environment/Dockerfile:24` says so explicitly). The spec's "root-only
   chmod 600" lighter fix is therefore insufficient, as the question warned.
   Shipped this pass: the offline-verifiable `calls >= 4` gate +
   `correctness=0`-unless-recovered + integer-only counter guard, which already
   makes the demonstrated `calls=0` forgery score 0.0
   (`tests/exploits/test_t6_forgery_regression.py` proves it). The heavier
   **compiled-dfetch-with-embedded-secret + HMAC nonce + grader-recompute +
   ordered-error-progression log** design is committed to in the `test.sh`
   header as **REBUILD-DEFERRED** (it cannot be exercised offline). The
   forge-with-N-junk-calls gap remains until that rebuild.
2. **T3 stale-memory seeding.** DEFERRED. The mechanical seeding (a TrialEvent
   hook or step-00 pre-step that writes the stale `45` into the hindsight bank
   for the trial's `eval-<harness>` group) needs sweep-driver wire-up + the
   `_assert_eval_scope` prod-safety guard + a rebuild/run to verify symmetry —
   all outside this pipeline. Only the offline T3 parts (spoiler strip,
   key-anchored sed, exclusivity grader) landed. The memoryless-degeneration
   fix (spec T3 #3 / acceptance 1b) stays open for the rebuild pass.
3. **S1 fragment delivery without a rebuild.** RESOLVED as **commit
   `lib/wipe_scratch.sh` + copy verbatim into each recall step's `workdir/`**
   (not inline). Paths were read from the rich-image home layout, not guessed
   (openclaw session JSONL under `$HOME/.openclaw`, hermes under `$HERMES_HOME`).
   No rebuild needed — these are in-container scripts uploaded with the step.
4. **T9 latency gate.** As-built the "gate" is the **per-problem
   calibration-offset round-trip**: the answer depends on a fact (`CAL-NN`→offset)
   that is not in the prose, served only by a registry lookup, so a prose-only
   parser collapses to chance (`tests/exploits/test_t9_parser_regression.py`).
   The actual **latency-bearing local lookup install** (a localhost endpoint or
   sleeping file-read wrapper — never external internet) **and budget
   calibration against a measured honest-serial run** are REBUILD/RUN-DEFERRED;
   the offline change guarantees the parser bypass is dead, not yet that the
   budget forces fan-out.
5. **Wave-2 rebuild/run dependency.** Confirmed and logged: tasks **3, 5, 6, 9
   stay BLOCKED for verdict-bearing n=5 runs** until the operator does the
   post-merge rebuild + sweep (T6 compiled helper, T9 gated-lookup install +
   budget, T5 corpus rebuild, T3 seeding, T4 token re-measurement). `RESULTS.md`
   was **not** modified on this branch (no sweep ran); per design decision 3 the
   operator records the deferral there when the severity-gated sweep runs.

### Lessons / gotchas for the next maintainer

- The agent really is root in T6 — any "make a file the agent can't write" fix
  is void without a compiled helper + a build-time secret stripped before agent
  start. Don't ship a chmod-only fix.
- `registry.json` (T9) is **answer-key-equivalent**: it must stay in `tests/`,
  never in `environment/`, or the parser bypass returns. `gen.py` writes it
  beside `answers.json` from the same RNG draw.
- `multi_step.py` treats a `setup.sh` non-zero exit as a *warning*, not a
  failure — so any load-bearing wipe needs an **independent assertion in
  `test.sh`** (the T8 `clamp_note*` probe pattern), not just `set -e` in setup.
- Acceptance criteria 1b, 6, 7 (seeding symmetry, T4 token re-measurement, the
  n=5 re-grid) are inherently run-dependent and remain unverified here.

### How to verify

Offline, on <run-host> (no docker, no sweep):
```
ssh <run-host>@LAN-IP 'cd ~/benchmarking/.baton-worktrees/baton-2026-06-11-core-eleven-second-adversarial-pass \
  && ~/benchmarking/harbor/.venv/bin/python -m pytest tests/ -q'
```
Good = **37 passed** (as-built: 37 passed in ~31s). This exercises every
recorded exploit-regression (T3/T6/T8/T9), the S1 wipe, the S2/S3 regrade
matrix, the S4 crash guards, and the S5 drift checks. The rebuild/run-dependent
acceptance criteria (T6 HMAC, T9 budget, T5 corpus, T3 seeding symmetry, T4
token count, n=5 Δ) are explicitly **deferred to the post-merge operator pass**.
