# Adversarial review — is this suite even useful to evaluate a harness? (2026-06-01)

6 parallel adversarial reviewers, biased to find fault (default verdict KILL/REWORK
unless a task CLEARLY forces a harness-dependent failure that spreads the score).
Verdict: **the suite, as built, does not effectively evaluate harnesses**, and a
provider-fairness regression means even a real score gap is currently
uninterpretable.

## CRITICAL — PROVIDER CONTAMINATION (fix before any run)

The deterministic-provider pin from task #46 (`backlog/done/2026-05-27-
deterministic-provider-routing.md`) was **reverted**. Evidence (file:line in the
provider-parity audit):
- Both harnesses hit OpenRouter on `deepseek/deepseek-v4-pro` (route is fair), BUT
  the upstream host is **unpinned for both** — `allow_fallbacks: true`, no
  `order`/`only`. OpenRouter load-balances across DeepSeek/Together/Novita/
  DeepInfra run-to-run → different KV-cache behavior + up to ~4x different per-token
  price. This is the EXACT v9 confound ("openclaw 0 cache hits vs hermes 21,504 on
  the same model — pure load-balancer luck") that #46 was written to kill.
- The routing objects are **not even identical**: hermes carries
  `require_parameters: true`, openclaw does not → the two sample from DIFFERENT
  candidate-host pools.
- temperature/top_p/max_tokens are unset in both → inherit each upstream host's
  defaults, which differ when the host differs. (reasoning_effort=high matches.)
- Cost is read from TWO sources: openclaw recomputes from live OpenRouter pricing;
  hermes self-reports its own `actual_cost_usd`. A cost delta can be pure
  accounting artifact.
**Verdict: CONTAMINATED.** Remediation = re-apply #46's pin identically in BOTH
baked configs (`harnesses/openclaw/openclaw.json` params.provider +
`harnesses/hermes/config.yaml` provider_routing): `order:[<one deepseek-v4-pro
host>], allow_fallbacks:false, require_parameters:true, data_collection:deny` —
and keep `lib/openclaw_openrouter.py` / `lib/hermes_no_install.py` constants in
sync. Re-verify via OpenRouter `/generation` that 100% of calls from BOTH hit the
same single host. Compute both harnesses' cost through the same path.

## TASK VERDICTS — ~4 keepers, ~23 kills, ~22 reworks of 50

The dominant failure: **MODEL-dominated, one-shot, saturates to 1.0 for both.** A
strong model solves a self-contained, fully-specified task identically in either
harness → the harness never has to navigate, iterate, recover, or manage context.
Graded rubrics only spread across MODEL quality, which is held constant, so they
collapse to 1.0 anyway.

### KILL (~23) — no realistic path to harness discrimination
- code-editing: fix-bug ×5, add-feature ×2 (tiny self-contained functions, fully
  specified → both ace). cli-tool-01, api-contract-01, readme-01, scaffold-
  document ×3 (one-shot deliverables; "multi-step" is illusory under
  reward_strategy="final"). marketing/email-copy-01 + backup-dr/restore-runbook-01
  (LLM-judge scores MODEL artifact quality → no spread; move to Track B).
- tool-orchestration: multistep-plan-execute ×3 (write a tiny CLI; "plan/implement/
  test" is decorative). skill-agent-authoring/sub-agent-01 (rote 16-file emit from
  a full table; fan-out never required or measured).
- real-world/ops: update-record-with-cleanup-01 (**ANSWER KEY LEAKED** — the
  expected CSV is shipped world-readable to the agent at `/app/.budget.expected.csv`).
  diagnose-from-logs-01 (the log narrates its own root cause in inline comments;
  grader matches copied keywords). failure-recovery-loop-01 (deterministic fail-1-3/
  succeed-4 → a fixed `for` retry loop is optimal; no adaptive recovery tested).
- conversation-persona/remember-facts-01 (already model-only; transcript pasted in
  one prompt).

### REWORK (~22) — salvageable but currently saturating or flawed
- memory-conversational-01/02/03: grader gives +1 for the right value and NEVER
  subtracts the confusable sibling value → a verbose model that dumps both scores
  1.0; the claimed "confused=0.42" is fiction. Also ~6 short turns fit any window
  → tests MODEL recall, not harness memory. Fix: precision-penalize on a labeled
  answer line; 15-20 distractor turns past the window; collapse 3→1.
- context-fill-02/03: good premise; grader is gameable (unanchored grep; sibling
  penalty only fires on same-line clean swap). Anchor scoring to labeled lines.
- tool-selection-01 / tool-sprawl-precision-01: answer half computable with plain
  `python3`/`wc` (bypasses tools entirely); correct tools have dead-obvious names;
  tool-selection still TELEGRAPHS the semver answer in the instruction. Make answers
  uncomputable without the tool; non-obvious tool names; require tool composition.
- skill-discovery-and-use-01: correct skill literally named `csv-structure-summary`
  matching the prompt → name-match, not description-reading. Neutral name + colliding
  decoys + a flag documented only deep in SKILL.md.
- sub-agent-parallel-decompose-01 (highest-value fix): parallelism bonus is
  MATHEMATICALLY INERT — `reward=min(1, base+0.15*par*base)` clamps to 1.0 for serial
  AND parallel when base=1.0. Make the budget infeasible serially so base<1.0 unless
  the harness fans out; score concurrency as a separate non-clamped dimension;
  verify concurrency from wall-clock, not self-reported timestamps.
- plan-then-revise-01: 4 one-line funcs → re-plan creates no friction. Build
  substantial scaffolding the revision partially invalidates + a conflicting earlier
  decision forcing a real revise-twice.
- code: refactor-multi-file-01 (3 toy files → blow up to 15-25 file package), pr-diff-
  review-01 (84-line diff, textbook vulns, regex grader gameable → 300-600 lines,
  subtle bugs, file:line citations), unit-tests-01 (4 mutants = 4 docstring lines →
  larger under-documented module, 20+ subtle mutants), dep-bump-breaking-01 (closest;
  scale to multi-module pkg with un-enumerated breakages + a real install/test/fix loop).
- research/ops: agentic-research + factual-lookup-cited (corpus fits one context →
  not "memory"; distractors are explicitly dated/flagged — one even has an "Editor's
  note: these figures are wrong". Balloon past one window, undated equally-authoritative
  decoys). find-contradictions-01 (single 2-page doc, intro telegraphs the distractor
  taxonomy). shell-pipeline-01 (22-line log, every edge case spelled out → scale to
  100k lines, remove the edge-case coaching). prompt-injection-resistance-01 (benign
  path = "send nothing" → free 1.0; must REQUIRE legitimate sends so exfil is a real
  off-path action; 60-email inbox, multi-step injections).
- data/security: pandas-sql-from-nl-01 + secret-scan-01 (scale data 50k rows / 200
  files or move to Track B).

### KEEP — genuine harness discriminators (conditional)
- context-fill-01 (1M-window eviction) — only if Harbor truly threads ingest steps
  into one growing conversation (VERIFY the threading model).
- multistep-proactive-preference-01 (ambient pref applied unprompted) — strengthen
  with more prefs the trigger phrases against.
- true-multi-turn-memory-write-01 (8 fields + late corrections + stale-rejecting
  grader + wipe) — add distance between facts and corrections.
- schedule-meeting-from-name-01 (multi-step state threading; honor the counter-
  proposal across a poll/reply loop) — the cleanest real discriminator found.
- _verify/reasoning-parity-01 — KEEP as an infra smoke test only; exclude from grid.

## STATUS / next-session pickup (2026-06-01)

**Phase 1 — provider contamination: FIXED** (commit b11f743). Both harnesses pinned
to one shared upstream `deepseek`, byte-identical in all 4 spots:
`harnesses/openclaw/openclaw.json`, `harnesses/hermes/config.yaml`,
`lib/openclaw_openrouter.py`, `lib/hermes_no_install.py` →
`{data_collection:deny, only:[deepseek], allow_fallbacks:false, require_parameters:true}`.
NOT YET PROVEN: (a) configs are baked into `harbor-agents-rich`
(`environments/agent-rich/Dockerfile`) → **rebuild the image** for the pin to take
effect; (b) run the fairness gate — confirm 100% of BOTH harnesses' calls hit
`deepseek` via OpenRouter `/generation`, and compute both costs through the same path.

**Phase 2 — deprecate + catalog 23 KILL tasks: DONE, non-destructive** (commit f1e6bd7).
Each KILL task.toml has `[metadata] status="deprecated"` + reason/date/doc. Nothing
deleted/moved. `task_catalog.py` surfaces them (26 active / 23 retired, red badge +
reason banner). **Operator must REVIEW the retired set before any removal.**
GAP: run configs (`configs/track-a-*.yaml`) select by category PATH, so a sweep
still picks up deprecated tasks — Harbor doesn't read `status`. Before any run,
exclude `status=deprecated` (active-only allowlist, or move after review) and have
`metrics/track_a_weighted.py` skip them.

**Phase 3 — rework ~22 salvageable: NOT STARTED** (task #89). Priority order:
1. CONTAINED SCORING FIXES first (stop the false 1.0s): memory-conversational-01/02/03
   (penalize sibling value on a labeled answer line), sub-agent-parallel-decompose-01
   (concurrency bonus is inert — make budget infeasible serially + score concurrency
   as a separate non-clamped dim), context-fill-02/03 (line-anchor the grep).
2. MEDIUM: remove residual telegraphing + undate decoys (agentic-research,
   factual-lookup-cited, find-contradictions), require legitimate sends
   (prompt-injection), remove edge-case coaching (shell-pipeline).
3. LARGE REBUILDS: scale past the 1M window (research corpora 150+ pages,
   shell-pipeline 100k lines, secret-scan 200 files, pandas 50k rows), multi-file
   repos + failing loops (refactor, pr-diff, unit-tests, dep-bump).
Each rework: validate via Harbor oracle (Docker build + plumbing). KEEP set
(context-fill-01, proactive-preference-01, true-multi-turn-write-01,
schedule-meeting-01) stays; reasoning-parity-01 = infra probe, exclude from grid.

## Cross-cutting design principles for a real harness discriminator
1. The answer must be **uncomputable without the harness-mediated path** (memory,
   tool, sub-agent, long-context). If `python3 -c` or a single read solves it, it's
   model-only.
2. **Exceed one context window**, or wipe between steps, so harness memory/context
   management — not the model's raw window — is what's tested.
3. **A failing loop the agent cannot one-shot** (install/test/fix, run-observe-revise)
   so navigation/iteration/recovery matters.
4. **Score the harness axis as a first-class, non-ceiling-clamped dimension** (don't
   add it as a bonus the correctness ceiling eats).
5. **No answer-key in the agent container; no self-narrating data; no edge-case
   coaching.** Verify graders aren't gameable by keyword-dumping.
6. Realistic SCALE and messiness (80 emails, 100k log lines, 150-page corpus,
   15-file repo), not vanilla 2-page synthetic filler.
