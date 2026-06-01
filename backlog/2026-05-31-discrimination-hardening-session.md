# Session record — discrimination hardening (2026-05-31)

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
  never touches prod groups juliet/yui/akane).
- Task Dockerfiles MUST `FROM harbor-agents-rich:latest` (baked openclaw.json +
  xrouter); prebaked silently boots default config.

## Remaining work (TODO after /clear)

- **Sharpen the rest of the suite** (in progress): apply the difficulty-raise
  pattern to remaining flat tasks — `multistep-memory-conversational-02` (weak
  3-step binary) + `-03` (precision-distractor treatment like -01); the binary
  high-weight tasks (`multistep-plan-execute-*`, `multistep-scaffold-implement-
  document-*`); tool-orchestration deeper load; etc. Document + commit each.
- **Run the two new memory tests on both harnesses** to evaluate (the proactive
  + stale-memory tests are built + locally validated but not yet LLM-run).
- **n=5 pass^k grid** on the sharpened focused set → publish `RESULTS.md` verdict
  (#79 → #81). The deferred money step (~$25–60).
- `multistep-memory-conversational-02/03` difficulty raise (not yet done).
