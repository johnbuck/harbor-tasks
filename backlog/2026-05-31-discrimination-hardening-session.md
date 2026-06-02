# Session record — discrimination hardening (2026-05-31)

- **Epic:** E4 — Task Suite

Full record of the harness-vs-model discrimination work done 2026-05-31, written
so the context survives a `/clear`. Sibling of
`2026-05-30-harness-vs-model-discriminating-suite.md` (the original spec) and
`2026-05-31-task-catalog-page.md`.

## North star (unchanged, Stop-hook enforced)

Prove the suite tells **harness quality** apart from **model quality**, then
publish the verdict. Both harnesses (openclaw, hermes) run the SAME model
(`deepseek/deepseek-v4-pro`), so any score gap is the harness, not the model.

## What shipped this session (commits on `main`, pushed)

1. **Task Catalog page** (`tools/task_catalog.py` → `task-catalog.html`, commit
   ce8fb58). Visual, drift-proof index of every task: what it asks, how it's
   graded (graded/binary badge), the oracle, the Dockerfile — modal viewer +
   client-side filter. Shared nav with `agent-status.html`. HTML is gitignored
   (regenerable); re-run `python3 tools/task_catalog.py`.

2. **Fixed `skill-discovery-and-use-01`** (commit 9515494) — verifier emitted a
   LIST-valued reward key (`skill_runs_logged: sorted(...)`); Harbor requires
   scalar-only reward values. Now `len(...)`. FOOTGUNS #38 updated with the
   list-valued variant (commit 3b29e77). This was the only real bug the
   focused-baseline n=1 surfaced; everything else is clean.

3. **Crash/timeout penalty + reliability axis** in `metrics/track_a_weighted.py`
   (commit 1ec5c15). A crashed/timed-out agent did NOT cleanly succeed even if
   the verifier read good filesystem state. Operator-set policy:
   - crash/timeout **+ complete** → effective reward **0.5**
   - crash/timeout **+ incomplete** → **0.0**
   - clean trials keep raw reward.
   "complete" = raw reward ≥ pass threshold. 0.5 is below threshold so it
   correctly fails pass^k. Report now carries `weighted_aggregate` (effective)
   vs `_raw`, `penalty_delta`, and a per-harness `reliability` block
   (crash_rate / timeout_rate / error_rate). Crash types: `NonZeroAgentExitCode`
   (= SIGABRT/segfault exit 134/139), `AgentTimeoutError`.

4. **Difficulty-raise rollout** (the discrimination lever — see Key Finding):
   - `fix-bug-with-failing-test-01` (commit 61bd32b): BINARY → graded rubric.
     New `count_words` contract (punctuation-only tokens excluded, hyphenated
     words count once) scored 0.4 visible + 0.4 hidden-contract + 0.2 quality
     (no test-tamper / signature / no-cruft). Hidden grader baked at
     `/opt/canonical/hidden_grader.py` (agent can't game it). Validated gradient:
     no-fix 0.20, naive off-by-one 0.83, full contract 1.00.
   - `multistep-memory-conversational-01` (commit 61bd32b): 8→14 planted facts;
     the 4 distractor turns now plant CONFUSABLE facts about other people
     (precision traps: Sam's shellfish+Mochi, Jess's Honda+Dune, Pat's Mar-4+
     Portland, a marine GEOlogist brother-in-law); recall 6→12 with a detail
     fact (car needs make+model+colour/year). Validated: confused 0.42, vague
     0.58, precise 1.00.
   - `context-fill-01/02/03` (commit 0241b4b): 11→18 markers + an UPDATE trap
     (a needle fact stated in chunk 1, corrected in chunk 14 — verifier credits
     only the LATEST; stale earns nothing) + a DRAFT decoy block (listing a
     decoy subtracts a point). Recall step renamed 12→19; cheat-proof setup.sh
     wipe preserved. /21 graded. Validated: perfect 1.0, degraded 0.714.
   - `failure-recovery-loop-01` (commit 0241b4b): binary → graded correctness +
     EFFICIENCY. Reads existing `/var/log/fetch.counter`; reward = 0.6·correct +
     0.4·efficiency, efficiency = clamp((15−attempts)/(15−4),0,1). Validated:
     recovered-in-4 1.0, flailed-12 0.71, never-recovered 0.0.

5. **Two new memory-reliability tests** (this commit):
   - `multistep-proactive-preference-01` — operator states 4 standing formatting
     prefs (ISO dates, 24h time, no-emoji headings, sign "D.H."), memorize-only;
     after distractors the final turn asks for a meeting announcement phrased in
     the NON-preferred form and never restates the prefs; setup.sh wipes notes
     so prefs must come from harness memory. Graded /4 on UNPROMPTED application.
     Validated: oracle 1.0, literal-echo 0.0, partial 0.5.
   - `multistep-stale-memory-vs-file-01` — agent reads + repeatedly USES
     `cache_ttl_seconds=45` from `/app/config.yaml` (cements it in memory), then
     step-04 setup.sh SILENTLY rewrites the file to 275 and asks for the current
     value. 275 = re-read ground truth (1.0); 45 = stale memory (0, flagged);
     other = hallucination (0, flagged). Targets the known openclaw failure of
     trusting outdated memory over re-fetching live file state. Validated:
     fresh 1.0, stale 0, hallucination 0.

## KEY FINDING — difficulty is the discrimination lever, not rubrics

The pilot proved it. The rubrics already existed (e.g. update-record has 18
sub-checks) — the tasks were just too EASY, so two competent harnesses aced
every check and everything flattened to 1.0. The real-harness n=1 spread-check
(`jobs/pilot-spread__*`):

| task | openclaw | hermes | result |
|---|---|---|---|
| fix-bug (binary→rubric) | 1.00 | 1.00 | BLUNT — both read the spec (code-editing is model-dominated, wt 0.5) |
| memory (difficulty-raise) | 1.00 (12/12) | **0.667 (8/12)** | **DISCRIMINATES Δ=0.33** |

And it was a GENUINE memory failure: hermes's recall trajectory shows it kept the
DISTRACTOR facts and lost the targets — *"The only cat mentioned was Mochi, and
that was Sam's cat"*, *"I don't recall [my allergy]. Sam is allergic to
shellfish"*, *"Pat's birthday is March 4, but I don't remember [mine]"*. Same
model both sides → that 0.33 is purely openclaw's recall+hindsight keeping facts
attributed where hermes's honcho+recall let distractors overwrite them.

**Takeaway:** binary→rubric is partial-credit *insurance* (catches a slip, feeds
pass^k) but does NOT manufacture a gap when both harnesses are perfect. Prioritize
**difficulty-raises on harness-sensitive axes** (memory precision, context
retention under update, recovery efficiency, proactive preference application,
stale-memory-vs-ground-truth). Treat binary→rubric as a cheap secondary upgrade
on model-dominated tasks.

## How to run / analyze (reproduce)

```bash
source ~/.config/infisical/infisical-identity.env
# one job per harness; n=5 for the real pass^k grid
CONFIG=$PWD/configs/track-a-focused.yaml N_ATTEMPTS=5 JOB_NAME=track-a-focused-n5 \
  tools/run_track_a.sh
# analyze (multiple --job-dir, reads effective reward + reliability):
uv run --project /tmp/harbor python metrics/track_a_weighted.py \
  --job-dir jobs/<name>__openclaw --job-dir jobs/<name>__hermes \
  --tasks-root tasks --weights configs/track-a-weights.toml
```

Jobs persist in `jobs/` (gitignored). Dashboard: `harbor view jobs --port 8089`
→ http://LAN-IP:8089. Agent-status + task-catalog pages: open the HTML
(or serve the repo root) — `python3 tools/agent_status.py` /
`python3 tools/task_catalog.py` to refresh.

## Hard rules carried forward (footguns)

- **Scalar-only reward.json** — flat dict of float/int. NO dict OR list values
  (Harbor pydantic rejects → trial errors reward=None). FOOTGUNS #38. Audit grep:
  `"key": {` AND `"key": [` AND `sorted(`/`list(`/`.keys()`/`.split(`.
- A cheap **n=1 trial is the only real validator** of a verifier — local
  oracle-eyeball misses the pydantic schema layer.
- `jobs_dir` must be absolute + persistent (`/tmp` is tmpfs, wiped on reboot).
- Memory wipes are **eval-* scoped only** (`hooks/wipe_memory_state.py` guards;
  never touches prod groups <prod-group>/<prod-group>/<prod-group>).
- Task Dockerfiles MUST `FROM harbor-agents-rich:latest` (baked openclaw.json +
  xrouter); prebaked silently boots default config.

## FULL-SUITE SHARPENING — COMPLETE (2026-06-01)

The entire suite has now been hardened (local validation only — oracle→1.0,
degraded→fractional for every task; no Docker/LLM runs). Catalog after:
**49 tasks, 48 graded / 1 binary-by-design, 33 hard + 15 medium, 0 errors.**
The lone "binary" is `multistep-stale-memory-vs-file-01` (read-fresh 1.0 / stale 0
/ hallucination 0 is a discrete probe, correct by design).

Commits (all on `main`, pushed) — each carries the per-task validated gradients:
- 51ea4ed memory-conversational-02/03 (precision distractors)
- 130625b tool-orchestration ×4 (binary→graded: plan-execute-01/02/03,
  tool-selection-01)
- 886c27e skill-authoring + real-world ×4 (sub-agent-01, sub-agent-parallel-
  decompose-01, schedule-meeting, prompt-injection)
- 19bc0af building-prototypes ×4 (scaffold-implement-document ×3 + cli-tool;
  dropped LLM judges for deterministic doc-matching graders)
- f8c1bde research/insights ×4 (agentic-research, factual-lookup-cited,
  find-contradictions, true-multi-turn-memory-write)
- 9f8facc migration/ops/data ×4 (dep-bump, diagnose-from-logs, pandas-sql,
  shell-pipeline)
- 128c0a0 code-editing ×7 (fix-bug 02–05, add-feature ×2, refactor)
- 4b826c8 api-contract, pr-diff-review, readme, secret-scan, unit-tests

Recurring sharpening techniques used: precision distractors (confusable
other-person facts), update-traps (value stated then corrected → require latest),
hidden contract graders baked at `/opt/canonical` (ungameable), precision+recall
scoring (over-flagging penalized via false-positive subtraction), mutation
coverage (a test suite that kills no mutant scores 0), efficiency budgets (retry
count), and decoy/red-herring items. Several latent bugs were fixed along the way
(a `grep -c` "00" reward-corruption, a regex self-collision, oracle output bugs).

## CONTEXT-MANAGEMENT REDESIGN — 1M-window saturation ladder (2026-06-01)

Operator review found the old `multistep-context-fill-01/02/03` were **not real
context tests**: telemetry filler explicitly labelled "long and mostly filler,
ignore it" + 18 random hex markers buried in it. That measures needle-search +
hex regurgitation, not "how does the agent behave when the context window fills
up." And 02/03 were structural clones of 01 (same engine, different marker
values) — three samples of one weak probe.

**Reframe:** context management = behaviour under context-window SATURATION. The
target model `deepseek/deepseek-v4-pro` has a **1,048,576-token (1M) window**
(confirmed via OpenRouter `context_length` + `top_provider.context_length`), so
the corpus is sized to **~1.3M cumulative tokens (~72K/report × 18) = ~1.25× the
window** — it overflows *before* recall, forcing each harness to compact /
externalise / truncate. That divergence-under-pressure is the harness signal.

Rebuilt as a **differentiated 3-rung ladder** (meaningful evolving project prose,
no "filler/ignore" framing; reports + notes deleted before recall; graded
precision+recall with stale/decoy penalties; generator `environment/gen_reports.py`):

- **01 — EVICTION** (PROJECT HELIOS, ground-station rollout). 12 current-state
  facts; STABLE-EARLY facts (kickoff/site/integrator/software, stated once wk1-8,
  never repeated) are evicted from a raw window → only a memory-externalising
  harness recalls them; UPDATE-TRAP facts corrected late. /12: +1 current, -1
  stale, -1 for the 2028-Q1 DRAFT decoy. Local gradient: oracle 1.0 / stale 0.0 /
  partial 0.33 / decoy 0.917.
- **02 — UPDATE-CHURN** (PROJECT VEGA, datacenter migration). Same saturation;
  nearly every fact corrected 2-3× (lead Reyes→Tanaka→Okafor; nodes 48→64→32;
  db PG14→PG16→Aurora; …). Must report the FINAL value, never an intermediate.
  /12: +1 final, -1 per stale (up to TWO/fact), -1 GCP decoy. Gradient: oracle
  1.0 / first-value 0.0 / intermediate 0.0.
- **03 — CROSS-TALK PRECISION** (PROJECTS ORION + LYRA interleaved). Both projects
  in every report with confusable parallel attributes, re-stated so both stay
  in-window. Line-anchored /12: +1 correct value on the slot line, -1 if the
  SIBLING project's value appears there (cross-attribution); Project-Nova DRAFT
  decoy. Gradient: oracle 1.0 / fully-swapped 0.0 / decoy 0.917.

**Validation:** local fixtures confirm each gradient; **Harbor oracle run
(`configs/validate-ctx.yaml`, Docker build + 19-step plumbing + reward schema, no
LLM) → all 3 reward 1.0, exceptions 0.** The oracle run caught a TOML bug that
local checks missed (03's description had `Lyra''s` inside a single-quoted TOML
literal → `''` terminated the string → 03 was *silently dropped* from the run;
FOOTGUNS #38 in action). Fixed; re-validated 1.0.

**Cost note:** these are now the most expensive tasks (cumulative ~1.3M-token
context per trial; with prompt caching ~$1-3/trial, ~$10-30 for the n=5×2 grid on
the three combined). Dial `LINES_PER_SECTION` in each `gen_reports.py` to resize.

## Remaining work (TODO after /clear)

- **Run the sharpened suite on both harnesses** — everything is locally validated
  (oracle/degraded) but FOOTGUNS #38 says only a cheap n=1 trial confirms the
  pydantic schema layer per task. Run `track-a-focused` (or the full suite) at
  n=1 first to catch any schema/heredoc surprise, then n=5 for the pass^k grid.
- **Run the two new memory tests** (proactive-preference, stale-memory-vs-file)
  on both harnesses to evaluate proactive application + stale-vs-ground-truth.
- **n=5 pass^k grid** → publish `RESULTS.md` verdict (#79 → #81). Deferred money
  step. With the suite now hard + graded, expect real spread + reliability gaps.
