# Harness-vs-model discriminating suite — eval the scaffolding, not the LLM

- **Epic:** E4 — Task Suite
- **Date:** 2026-05-30
- **Status:** INSTRUMENT PROVEN (interim), n=5 pass^k pending budget. As of
  2026-05-31:
  - n=1 smoke (94 tasks) ran clean (0 infra errors) → **36/45 BLUNT**, confirming
    the pre-sharpening suite was model-dominated. Two real discriminators found
    (failure-recovery retry-efficiency; find-contradictions precision) + robust
    **efficiency split (openclaw 0.35–0.62× hermes cost for equal results)**.
  - **All 15 high-weight BLUNT tasks sharpened** → graded scoring + category
    stressor (see Sharpening playbook); all oracle-validate.
  - **Proven discriminator:** `memory-conversational-01` openclaw 6/6 vs hermes
    3/6, **Δ=0.50**, same model/cost.
  - **Key finding:** the harness gap is *reliability* (pass^k), not single-run
    reward — the same tasks flip pass/fail between n=1 runs (hermes inconsistent,
    openclaw steady). n=1 is a coin-toss; **n=5 is the real grid.**
  - Live results: `RESULTS.md` + dashboard `harbor view jobs --port 8089`.
  - **Remaining:** the focused **n=5 pass^k** run (~$60; budget decision open —
    recommend n=5 on the ~7 variance-showing tasks for ~$25) → then publish the
    final verdict (#79 → #81).
  - Footguns resolved this phase: FOOTGUNS.md #35 (FROM rich), #36 (env
    auto-export), #37 (wipe-hook agent-name + honcho/hindsight wipe bugs + eval-
    scope guard), #38 (scalar-only reward.json), #39 (tmpfs/absolute jobs_dir),
    #40 (dashboard lifecycle).
  - **Critical build rule (still load-bearing):** every task Dockerfile must
    `FROM harbor-agents-rich:latest`, NOT `harbor-agents-prebaked` — only rich
    has the baked openclaw config with the `xrouter` custom provider.
- **Origin:** Operator — "the model is less important than the harness itself even
  though the harness would behave differently on a per-model basis." After the
  recall hindsight-parity work shipped (P1–P4, [`done/2026-05-29-recall-hindsight-style-plugin.md`](done/2026-05-29-recall-hindsight-style-plugin.md)),
  we audited the first-sweep task suite and found most categories are
  **model-dominated**: same model + different harness should produce indistinguishable
  scores on them. The harness comparison signal is concentrated in 3 categories
  (`context-management`, `tool-orchestration`, `skill-agent-authoring`).
- **Related specs:**
  [`2026-05-27-task-suite-design.md`](2026-05-27-task-suite-design.md),
  [`2026-05-27-context-management-category.md`](2026-05-27-context-management-category.md),
  [`2026-05-29-new-eval-tasks-subagent-research.md`](2026-05-29-new-eval-tasks-subagent-research.md),
  [`2026-05-29-eval-infra-stack.md`](2026-05-29-eval-infra-stack.md).

## Goal — Definition of Done

**Prove the suite can tell harness quality apart from model quality — then
publish the verdict.** (Operator-set north star, 2026-05-31: *prove the
instrument*, not merely make a harness decision or ship an artifact.)

Both harnesses run the **same model** (deepseek-v4-pro), so any gap — in
success, reliability, OR efficiency — is attributable to the harness, not the
model.

**The instrument discriminates on three axes** (`metrics/track_a_weighted.py`
computes all three):
1. **Success** — weighted-aggregate reward split (the ≥10% headline bar).
2. **Reliability** — pass^k (n=5): does one harness pass 5/5 where the other
   passes 3/5 on the same task? Reward-mean can tie while reliability separates.
3. **Efficiency** — cost/token per task. Same model ⇒ a cost gap is a *pure*
   harness signal (early smoke read: reward tied but openclaw $0.35 vs hermes
   $0.62/task, 0.57× — hermes's scaffold burns ~75% more for identical results).
   Binary verifier tasks saturate reward (both ace ⇒ BLUNT), so efficiency is
   often where competent-harness-vs-competent-harness actually separates.

The instrument is **proven** when:

1. **Track A completes at n=5 (pass^k)**, both harnesses, **0 infra errors**.
2. The weighted grid shows a **≥10% weighted-aggregate split that is reliable
   under pass^k** (not single-trial variance), concentrated in the
   harness-discriminating categories: `context-management`,
   `tool-orchestration`, `skill-agent-authoring`, the memory-write
   `conversation-persona` shape, and `real-world-workflows`.
3. **RESULTS.md** is published — per-category + per-difficulty, pass^k
   reliability columns, plain-English verdict — and is reproducible from one
   command.

### The prove-the-instrument loop

A flat result is NOT "done" — it's a signal to diagnose, then sharpen:

```
n=1 smoke  → grid populates, 0 infra errors, eyeball split direction
n=5 pass^k → the real measurement
analyze split:
  ≥10% reliable split on discriminating categories → INSTRUMENT PROVEN → publish
  <10% → diagnose BEFORE concluding "harnesses are equivalent":
    a. per-task headroom: oracle=1.0 but harnesses tie (BLUNT) vs both fail
       (TOO HARD) vs genuine tie (EQUIVALENT)?
    b. refit category weights toward highest-variance discriminating tasks
    c. flag/replace blunt tasks
    d. re-run → repeat
```

**Critical guardrail:** "the harnesses are equivalent" is a valid conclusion
*only after* the instrument is shown capable of detecting a difference. The
mechanically-harness-dependent tasks must separate first — e.g.
`true-multi-turn-memory-write-01`, where hermes invokes its honcho/recall write
path and a memoryless harness *physically cannot* recall the planted facts. If
even those are flat, the instrument is broken (wiring/contamination/scoring),
not the harnesses equivalent. Memory contamination is the top confound — see the
`wipe_memory_state` hook + its eval-scope guard (FOOTGUNS #37).

## Sharpening playbook (2026-05-31, from smoke n=1)

The smoke proved plumbing (0 errors) and surfaced two REAL discriminators
(efficiency: oc/he 0.62× cost; failure-recovery: hermes 51 retries vs openclaw
4 → reward 0 vs 1). But **36/45 tasks came back BLUNT** (both harnesses ace at
1.0). Diagnosing the high-weight BLUNT tasks revealed the systemic cause:

**Tasks let the agent offload state to the filesystem, bypassing the harness.**
`context-fill-01` tells the agent to write facts to `/app/notes.md` during
ingest and grep them back at recall — so the 210K-token context window and the
memory backend (recall/hindsight/honcho) are NEVER stressed. It tests "can the
model write+read a file," which every harness aces. Same antipattern as the
`remember-facts-01` `single-turn-proxy` flaw, one layer down.

Sharpening levers (apply per category, validate each discriminates via a cheap
single-task 2-harness n=1 trial BEFORE the focused n=5):
1. **Remove filesystem crutches** — state must survive through the harness's own
   memory across fresh-process steps (each Harbor step is a fresh `agent` call;
   only the memory backend or files carry state — so kill the files).
2. **Inject recoverable failures** — the proven `failure-recovery-loop` pattern;
   reward gates correctness on a retry/step budget, so a thrashing harness fails.
3. **Overflow / distract** — enough planted facts + distractors that retrieval
   *precision* (not just storage) separates harnesses.

Targets (w≥2.0, smoke-BLUNT): context-management ×3, real-world-workflows ×3,
skill-agent-authoring ×3, tool-orchestration ×2, conversation-persona ×3,
insights-research ×1, research-rag ×1. Controls (w=0.5: code-editing, marketing,
docs, …) stay BLUNT by design — they're model-dominated baselines.

### VALIDATED 2026-05-31 — the playbook works (Δ=0.50)

First sharpened exemplar `multistep-memory-conversational-01`: 3 facts/1
distractor → **8 facts / 4 distractor turns / graded 6-fact recall**. Empirical
2-harness n=1 (fixed wipe hook, clean memory):

| harness | reward | recalled | cost |
|---|---|---|---|
| openclaw | 1.0 | 6/6 | $0.100 |
| hermes | 0.5 | 3/6 | $0.104 |

**Δ=0.50, same model, near-identical cost** — openclaw's recall+hindsight beat
hermes's honcho+recall on retrieval under load. Two lessons locked in:
1. **Graded scoring is mandatory.** A binary all-6 verifier scores both 0
   (both <6) → still BLUNT. The *fraction* (6/6 vs 3/6) is the signal.
2. The "don't write facts to a file" instruction is respected — hermes lost
   facts to memory, didn't cheat to disk. So the instruction-based memory forcing
   is sound even on a shared filesystem (resolves the context-fill cheat worry).

Replicated to `-03` (fresh facts, same structure, oracle-validated). Pattern is
now the template for the remaining memory/recall-dependent targets.

### ALL 13 high-weight BLUNT tasks sharpened (2026-05-31)

Every w≥2.0 BLUNT task converted to graded scoring + a category stressor; all
oracle-validate (oracle→1.0, partial→fractional), keep `FROM harbor-agents-rich`,
difficulty=hard:
- **conversation-persona** ×2 (`-01` empirical Δ=0.50, `-03`): 8 facts / 4
  distractors / graded 6-fact recall. (`-02` already discriminated.)
- **context-management** ×3 (`context-fill-01/02/03`): removed the `notes.md`
  crutch; a recall-step `workdir/setup.sh` **deletes /app/chunks + notes BEFORE
  the recall agent runs** (Harbor runs `steps/<n>/workdir/setup.sh` pre-agent —
  `multi_step.py:300`), so the 11 markers must come from the harness memory
  backend, not a re-read. Graded recall of 11 markers + 3 needle facts = /14.
- **tool-orchestration** ×2: tool-sprawl 28→57 decoys, graded `0.5·answer +
  0.5·tool_f1`; plan-then-revise graded /8 over functional + cleanup + re-plan.
- **skill-agent-authoring** ×3: sub-agent 10 files ×4 structural checks (/40);
  parallel-decompose 20 files ×3-stage (/60) with throughput scaled by base;
  skill-discovery 1 correct skill among 9 decoys + breadcrumb-proven use (/16).
  (Also dropped live-Anthropic LLM-judge deps → deterministic.)
- **real-world-workflows** ×3: update-record 30 rows/19 checks; prompt-injection
  4 attacks/4 graded axes; schedule-meeting counter-proposal cross-step state /14.
  (Fixed a `responder.py` SyntaxError that made schedule-meeting unsolvable.)
- **insights-research** ×1 (8 contradictions + 2 distractors, /8) + **research-rag**
  ×1 (8 facts each needing a citation, /8).

10 of these were authored by 4 parallel subagents; all batch-verified (parse,
rich base, graded). **Caveat:** oracle-valid + graded makes discrimination
*possible* (no longer saturated); whether each actually separates the harnesses
is empirical — the focused n=1 then n=5 measures it. Only `-01` is proven so far.

## Problem

A harness comparison is only credible if the tasks **discriminate the harness**,
not the model. Today's suite has the inverse property in most categories:

- `code-editing` has 8 tasks (the most depth in the suite) but the model writes
  the code; differences between openclaw and hermes wash out in noise. The
  `sweep-coding-5` result was effectively tied (166.8s/$0.219 vs 179.8s/$0.211).
- `marketing`, `documentation`, `code-spec-review`, `test-authoring`,
  `building-designs`, `compliance-security` each have 1 task and produce text the
  model writes — the harness is invisible.
- `conversation-persona/remember-facts-01` is tagged `single-turn-proxy`: the
  multi-turn conversation is **embedded in the instruction as a transcript**,
  so the harness's memory write path (recall `add_memory`, hindsight `retain`,
  honcho native provider) is **never invoked**. The recall hindsight-parity work
  ships with no eval that actually exercises it.
- `context-management` is the strongest pure-harness shape and has 3 tasks
  authored, but the category is currently DEFERRED out of the first sweep.

These are confounds — not "we don't have enough tasks." Adding more model-dominated
tasks won't fix it. We need shapes deliberately designed to expose harness
behavior: planning, tool selection precision, memory write proactivity,
memory retrieval across true session boundaries, sub-agent delegation, context
compaction, skill discovery, and failure recovery.

## Scope

**In:**

1. A reusable rubric — what makes a task "harness-discriminating" and how to
   tag/score it.
2. **Eight new task shapes** (with rationale + verifier sketches) that target the
   identified gaps.
3. Re-classification of the existing 17-category inventory by harness signal
   weight (S=Strong / M=Mixed / W=Weak) so the **sweep weighting** can be set
   per category instead of treating every task as equal.
4. A **two-track sweep config** — Track A (harness-discriminating, 8–12 shapes,
   weighted heavily) and Track B (general capability, all 17 categories, for
   public-facing reporting).
5. Action items to fix or retire load-bearing model-dominated tasks
   (specifically `remember-facts-01`'s single-turn-proxy property).
6. A "Literature" section with findings from the
   harness/memory-eval research subagent (added when the subagent reports).

**Out:**

- Implementing all eight new shapes in this spec. Implementation lands in
  follow-up specs per shape (or batched).
- Retiring code-editing tasks — they remain in the suite for general-capability
  reporting (Track B). They just lose weight in Track A.
- Changing the existing verifier/judge infrastructure
  ([`tests/test.sh`](../tasks/code-editing/fix-bug-with-failing-test-01/tests/test.sh),
  `tests/llm_judge.py` → `claude-opus-4-7`).

## Design decisions

### Rubric — when is a task harness-discriminating?

A task is **harness-discriminating** when at least two of these are true:

1. **Tool/MCP routing** — the task offers many candidate tools and the harness
   must select the right ones. (Recall, hindsight, honcho, browser, search,
   shell, file, fetch — bad routing burns turns, good routing is invisible.)
2. **Memory write proactivity** — the user gives information the harness should
   capture without being told to. Score = whether `add_memory` / `retain` /
   honcho native provider was actually called.
3. **Memory retrieval across true session boundaries** — turn 1 in session A
   writes; turn 1 in session B (fresh context, same agent identity / group_id)
   must retrieve. The transcript MUST be true multi-session, not embedded.
4. **Planning + revision** — the task forces a plan, then forces a change
   mid-execution. Harnesses with explicit planning structures (hermes kanban,
   openclaw sessions) revise; harnesses with blind-execution loops thrash.
5. **Sub-agent delegation** — parallel-decomposable work where serial execution
   blows the turn budget. Score = wall-clock + whether child sessions exist.
6. **Context compaction** — long-running session where the harness's window
   exhausts. Does it compact, truncate, summarize, or fail?
7. **Skill discovery + invocation** — task is trivially solved by a skill the
   harness ships. Did the harness use the skill, or solve from scratch?
8. **Failure recovery** — tool returns an error once, then succeeds. Did the
   harness retry, escalate, or give up?

A task that meets none is **model-dominated** — keep it for Track B reporting,
do not weight it in Track A.

### Re-classification of the existing 17 categories

| Category | Tasks | Track A weight | Why |
|---|---|---|---|
| **context-management** | 3 | **3.0** | Pure-harness; promote out of DEFERRED |
| **tool-orchestration** | 4 | **3.0** | Tool selection + planning |
| **skill-agent-authoring** | 1 | **3.0** | Sub-agent (#55 design) hits delegation |
| **conversation-persona** | 4 | **2.0 → 3.0 after fix** | Strong IF true multi-turn; currently broken via `single-turn-proxy` |
| **research-rag** | 1 | 2.0 | Memory + retrieval; only 1 shape today |
| **insights-research** | 1 | 2.0 | Memory + reasoning |
| **ops-debugging** | 2 | 1.5 | Shell/MCP routing some signal |
| **building-prototypes** | 4 | 1.5 | MCP usage, but model writes code |
| **data-analytics** | 1 | 1.5 | Tool + analysis split |
| **migration** | 1 | 1.5 | Multi-step gives some signal |
| **backup-dr** | 1 | 1.5 | Runbook execution |
| **code-editing** | 8 | **0.5** | Model-dominated; keep for Track B |
| **marketing** | 1 | 0.5 | Model-dominated |
| **documentation** | 1 | 0.5 | Model-dominated |
| **code-spec-review** | 1 | 0.5 | Model-dominated |
| **test-authoring** | 1 | 0.5 | Model-dominated |
| **building-designs** | 1 | 0.5 | Model-dominated |
| **compliance-security** | 1 | 0.5 | Model-dominated |

Weight is a multiplier on the per-task reward when aggregating to the harness
score. A weight of 0.5 doesn't remove the task — it down-weights its
contribution. Track B uses all weights = 1.0 (general capability).

### Eight new task shapes to author

Each rationale → which rubric criteria it hits → verifier sketch.

#### 1. `true-multi-turn-memory-write` (conversation-persona)

- **Hits:** memory write proactivity, true session boundaries.
- **Replaces** the single-turn-proxy property of `remember-facts-01`.
- **Shape:** Harbor `steps/` task with N real turns. Turns 1–5: user shares
  facts in conversation ("I'm vegetarian", "I have a cat named Sushi", "I work
  east-coast hours"). Turn 6 (new step, fresh context per the harness): user
  asks a question that requires the recalled facts ("plan me a dinner I can eat
  during a 3 PM PT meeting").
- **Verifier:** (a) tool-call log inspection — count `add_memory` /
  `retain` / honcho-write calls during turns 1–5 (proactivity score); (b) judge
  rubric on turn 6 answer requiring all relevant facts; (c) memory backend
  inspection — query recall/hindsight/honcho for the agent's group_id, assert
  facts persisted.

#### 2. `tool-sprawl-precision` (tool-orchestration)

- **Hits:** tool/MCP routing.
- **Shape:** register 30+ MCP tools (varied signatures, mostly irrelevant);
  task requires exactly 2 of them. Decoy tools are plausible-sounding.
- **Verifier:** tool-call log → precision (calls to the 2 correct tools /
  total tool calls) and recall (correct tools called / 2). Score =
  `2 · P · R / (P + R)`. Plus a correctness check on the final output.

#### 3. `failure-recovery-loop` (ops-debugging)

- **Hits:** failure recovery, planning + revision.
- **Shape:** MCP tool that fails the first N times (deterministic, harness sees
  503/timeout/garbled output), then succeeds. Two variants: transient-error
  (retry-appropriate) and persistent-error (escalation-appropriate).
- **Verifier:** tool-call log — turn count to success; whether the harness
  retried sensibly (not infinitely); on persistent-error, whether the harness
  abandoned the path and tried an alternate route. Reward = step function.

#### 4. `plan-then-revise` (tool-orchestration)

- **Hits:** planning + revision.
- **Shape:** task gives the harness 4 subgoals. After subgoal 2 completes,
  the environment changes (file appears, prior assumption invalidated) so
  subgoals 3–4 must be replanned.
- **Verifier:** scan harness session/plan artifacts (openclaw `sessions/`,
  hermes `kanban/`) for evidence of plan revision. Plus correctness on final
  state.

#### 5. `skill-discovery-and-use` (skill-agent-authoring)

- **Hits:** skill discovery + invocation.
- **Shape:** the rich harness image ships a skill that solves the task in one
  call (e.g. a `format-csv-as-table` skill). Task description does not mention
  the skill by name. The harness can solve manually or invoke the skill.
- **Verifier:** correctness + a bonus for skill invocation observed in the
  tool-call log. Hermes (skills are a first-class system) vs openclaw (skills
  via the `skills` field in `openclaw.plugin.json`) should split here.

#### 6. `sub-agent-parallel-decompose` (skill-agent-authoring)

- **Hits:** sub-agent delegation, planning + revision.
- **Shape:** task #55 from
  [`2026-05-29-new-eval-tasks-subagent-research.md`](2026-05-29-new-eval-tasks-subagent-research.md).
  Already scoped. Specifically: N=10 independent inputs that benefit from
  parallel processing. Serial completion exceeds the turn budget.
- **Verifier:** per-subtask correctness + child-session artifact check
  (openclaw `sessions_spawn`, hermes `delegate_task`). Wall-clock budget that
  rewards parallelism.

#### 7. `context-fill-and-compact` (context-management)

- **Hits:** context compaction, planning + revision.
- **Shape:** sustained multi-step task that intentionally fills 80% of the
  context window mid-run (large file reads, log dumps). Final step requires
  recall of detail from the start of the session.
- **Verifier:** does the harness still solve the final step? Inspect session
  artifacts for compaction events. (Existing
  [`2026-05-27-context-management-category.md`](2026-05-27-context-management-category.md)
  authoring covers the shape.)

#### 8. `live-research-with-memory` (research-rag)

- **Hits:** memory write proactivity, tool/MCP routing, planning + revision.
- **Shape:** task #56 from
  [`2026-05-29-new-eval-tasks-subagent-research.md`](2026-05-29-new-eval-tasks-subagent-research.md)
  — agentic research using browser/CDP + search + memory. Requires the
  browser/CDP work from [`2026-05-29-eval-infra-stack.md`](2026-05-29-eval-infra-stack.md)
  (task #54) and the memory stack (shipped).
- **Verifier:** citation grounding + memory-write tool-call check + judge
  rubric for synthesis quality.

### Two-track sweep config

Both tracks share task instances; weighting differs.

- **Track A — harness-discriminating** (`configs/track-a-harness.yaml`):
  weights from the table above; aggregate score is `Σ(weight · reward) / Σ(weight)`.
  Primary harness comparison runs here. Expected to **split** openclaw vs
  hermes meaningfully.
- **Track B — general capability** (`configs/track-b-general.yaml`):
  weight = 1.0 across all categories. For public-facing reporting / quick
  smoke checks. Expected to look tied (because most tasks are
  model-dominated and the model is held constant).

The split is a **methodology decision**, not a code change — it's two YAML
configs over the same `tasks/` tree.

### Fix `remember-facts-01` immediately

The `single-turn-proxy` tag is documented as "True multi-turn deferred." That
deferral was acceptable when the eval was probing model recall comprehension.
For a harness comparison, it's actively misleading — it tells us nothing about
recall/hindsight/honcho. Fixes (pick one):

- **A. Retag + downweight** — change `single-turn-proxy` → `model-only`, set
  Track A weight to 0.5, leave the task. Cheapest.
- **B. Replace with true-multi-turn-memory-write** (shape #1 above). Harbor's
  `steps/` shape supports multi-step. ~1–2 days.
- **C. Keep both** — leave `remember-facts-01` in Track B (general capability)
  and author the new shape for Track A.

Recommendation: **C**. Lowest-disruption, preserves existing sweep results, and
the new shape carries the harness signal.

### What we are NOT doing

- Not retiring any existing tasks. Track B preserves them for general reporting.
- Not changing the model. deepseek-v4-pro stays pinned across both harnesses;
  reasoning on; OpenRouter `data_collection: deny` for both.
- Not building all eight shapes in one spec. Each shape gets its own
  implementation spec (or is batched).

## Acceptance criteria

- [ ] This spec reviewed by an adversarial subagent (catch confounds in the
      rubric or weighting).
- [x] Literature section populated with subagent research findings (done
      2026-05-30 — HAL, τ-bench, AHE, SkillsBench, LongMemEval, Mem0, Zep,
      MEM2ACTBENCH).
- [ ] `configs/track-a-harness.yaml` + `configs/track-b-general.yaml` authored
      with the weights above; round-trip with `harbor run`.
- [ ] `remember-facts-01` retagged from `single-turn-proxy` → `model-only`.
- [ ] At least three of the eight new shapes authored, oracle-validated, and
      first-instance run on both harnesses.
- [ ] First Track A sweep result shows **non-trivial harness split** (target:
      ≥10% aggregate-score delta between openclaw and hermes, or a clear
      qualitative difference in tool-call patterns).
- [ ] **(Harbor-native)** Track A sweeps run with `n_attempts: 5` so
      `compute_pass_at_k_by_evals` reports pass^2, pass^4, pass^5. No code; YAML
      change.
- [ ] **(Harbor-native)** Every task instance carries a
      `difficulty: easy|medium|hard` value in its `task.toml`
      `[metadata]` (free-form passthrough); Track A's uv-script metric reads
      it and emits per-tier breakdowns.
- [ ] **(Small code, uses Harbor extension point)** `hooks/wipe_memory_state.py`
      registered as a `TrialEvent.START` hook in the sweep driver; wipes the
      agent's recall group, hindsight bank, and honcho workspace before each
      trial. Eliminates the cross-run contamination confound.
- [ ] **(Documentation)** Judge-family separation noted in the run report
      (agent = deepseek-v4-pro, judge = claude-opus-4-7 — different families,
      so no preference leakage; flag if either changes).
- [ ] **(Small code, uses Harbor extension point)** `metrics/track_a_weighted.py`
      authored as a `MetricType.UV_SCRIPT` metric (~80 LoC); reads
      category weights from `configs/track-a-weights.toml`, emits weighted
      aggregate + per-difficulty-tier breakdown.

## Harbor alignment — what's native vs. what we add

Operator concern (2026-05-30): "we're not trying to get super far away from the
Harbor framework and make wild adjustments." This section maps every
requirement in the spec to a Harbor primitive so we know what's free vs. what
needs code. **Verdict: almost every requirement maps to something Harbor
already ships. Two things require small code, none require a framework fork.**

| Requirement | Harbor primitive | Source |
|---|---|---|
| **`pass^k` reliability runs** | `JobConfig.n_attempts: int = 1` runs every trial k times; `harbor.utils.pass_at_k.compute_pass_at_k_by_evals` computes pass^k post-hoc on binary (0/1) rewards. Eligible k values: powers of 2 plus multiples of 5 up to `n_attempts`. | `src/harbor/models/job/config.py:254`, `src/harbor/utils/pass_at_k.py` |
| **True multi-turn / multi-session memory tasks** | `steps/` directory with `[[steps]]` array-of-tables in `task.toml`. Each step has its own `instruction.md`, `tests/`, optional `workdir/setup.sh`. Container env is shared across steps (intentional, for memory tests). `min_reward` gates early-stop. `multi_step_reward_strategy: "mean" \| "final"` rolls up to a trial-level reward. | `docs/content/docs/tasks/multi-step.mdx`, `src/harbor/trial/multi_step.py` |
| **Per-trial memory snapshot/restore (no cross-run contamination)** | Trial lifecycle hooks: `TrialEvent.{START, ENVIRONMENT_START, AGENT_START, VERIFICATION_START, END, CANCEL}` with `Job.add_hook(event, callback)`. A `TrialEvent.START` callback can wipe the agent's recall group, hindsight bank, and honcho workspace via their HTTP APIs. **Small code to write (~50 LoC callback)**, no Harbor change. | `src/harbor/trial/hooks.py`, `src/harbor/job.py:138` |
| **Multi-axis rewards** (correctness + tool_selection + proactivity) | `rewards` is a `dict[str, float]`. `min_reward` accepts a dict. `multi_step_reward_strategy: "mean"` does per-key means across steps. Verifier writes `reward.json` (or `reward.txt` for 1D). | Already in use in our `tests/test.sh` pattern |
| **Track A weighted aggregation by category** | `JobConfig.metrics: list[MetricConfig]`. `MetricType.UV_SCRIPT` runs a `uv run <script>` with rewards as JSONL stdin and reads a `metric.json` back. We write `metrics/track_a_weighted.py` that reads category weights from a config and produces a weighted mean. **Small code to write (~80 LoC).** | `src/harbor/models/metric/config.py`, `src/harbor/metrics/uv_script.py` |
| **Track B uniform aggregation** | `MetricType.MEAN` — native, default. Zero code. | `src/harbor/metrics/mean.py` |
| **Two "track" sweep configs** | Two `job.yaml` files referencing the **same `tasks/` tree** with different `metrics:` lists. Not a Harbor concept; just two files. | — |
| **Difficulty stratification** | `task.toml` already has a free-form `[metadata]` table (we use it for `category`, `shape`, `tags`). Add `difficulty: easy\|medium\|hard`. Our Track A uv-script can read this from each task's TOML and emit per-tier breakdowns alongside aggregate. | We already use `[metadata].category` etc. |
| **Tool-call inspection in verifier** (for proactivity/precision scoring) | Harbor saves the agent's full trajectory to `<trial>/agent/trajectory.json` (documented format). Our `tests/test.sh` (or `llm_judge.py`) can read it from the verifier container — already mounted alongside the task workspace. **No code change**, just author the verifier to inspect it. | `docs/content/docs/agents/trajectory-format.mdx` |
| **Judge model = different family from agent** | `tests/llm_judge.py` already calls `claude-opus-4-7` while the agent runs deepseek-v4-pro — a methodology choice we already made, just document it explicitly. | Existing convention |
| **Cost reporting** | Already implemented in our `OpenClawOpenRouter` / `HermesNoInstall` adapters; viewer surfaces tokens + $ per trial. | Tasks #41, #43, #44 (all completed) |

### Two things in the spec needed correcting

1. **"Two-track sweep config"** was framed as a methodology gadget. It's just
   two `job.yaml` files over the same task tree with different `metrics:` lists
   (one `MetricType.MEAN`, one `MetricType.UV_SCRIPT` pointing at our
   weighted-mean script). Not a Harbor extension.

2. **"pass^k as a new acceptance criterion"** was framed as something we'd build.
   Harbor already implements it (`n_attempts` + `compute_pass_at_k_by_evals`).
   Acceptance criterion stays — it's setting the right config, not writing code.

### The only code we write

Two small Python files, both following existing Harbor extension points:

1. `metrics/track_a_weighted.py` (~80 LoC) — `uv-script` metric that reads
   category weights from a config TOML and produces a weighted mean +
   per-difficulty-tier breakdown. Pattern is the `MetricType.UV_SCRIPT` contract
   in `src/harbor/metrics/uv_script.py`.
2. `hooks/wipe_memory_state.py` (~50 LoC) — `TrialEvent.START` hook callback
   that wipes the agent's recall group, hindsight bank, and honcho workspace
   for the eval group_id (`eval-openclaw` or `eval-hermes`). Wires up in the
   sweep driver script via `job.add_hook(TrialEvent.START, wipe_memory_state)`.

Neither touches Harbor source. Both are repo-local additions.

### Things we are explicitly NOT doing

- Not forking Harbor.
- Not extending `JobConfig` or `MetricConfig`.
- Not changing the trial runner.
- Not adding a "track" concept to the framework — tracks are just two YAMLs.
- Not changing the trajectory format or verifier sandboxing.

## Literature — published methodology + benchmarks

A research subagent surveyed published work on harness-vs-model evaluation and
agent-memory benchmarks (2026-05-30). Key findings below; many of the eight
proposed shapes are validated by published precedent, and several methodology
patterns are strong enough to fold into the spec as acceptance criteria.

### Benchmarks that establish the harness-vs-model framing

| Benchmark | Why it matters here | URL |
|---|---|---|
| **HAL** (Princeton, Oct 2025) | 9 models × 9 benchmarks × multiple scaffolds, 21,730 rollouts. Establishes a **three-axis decomposition** (model × scaffold × benchmark) — exactly the framing harbor-tasks needs. Reports cost + reliability + robustness alongside accuracy. | [arxiv.org/abs/2510.11977](https://arxiv.org/abs/2510.11977), [hal.cs.princeton.edu](https://hal.cs.princeton.edu/) |
| **τ-bench / τ²-bench** (Sierra) | Customer-service tool+policy tasks. Introduces **`pass^k`** (all k trials succeed) as a reliability metric. State-based eval (DB end-state vs goal). Already in our backlog as [`2026-05-28-tau3-bench-integration.md`](2026-05-28-tau3-bench-integration.md). | [arxiv.org/abs/2406.12045](https://arxiv.org/abs/2406.12045), [github.com/sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) |
| **SWE-bench Pro scaffold spread** | Same Claude Opus 4.5 model across 4 frameworks → 9.5-pt spread; broader same-model/different-scaffold studies show up to 30-pt variance. Direct empirical support for the framing. | [morphllm.com/swe-bench-pro](https://www.morphllm.com/swe-bench-pro) |
| **AHE — Agentic Harness Engineering** | Four-component swap ablation: long-term memory **+5.6pp**, tools **+3.3pp**, middleware **+2.2pp**, system prompt **−2.3pp**. Effects flip sign by difficulty tier — single aggregate hides the signal. | [arxiv.org/abs/2604.25850](https://arxiv.org/abs/2604.25850) |
| **SkillsBench** | 3 commercial harnesses × 7 models × {no-skill, with-skill, self-gen}. Direct precedent for our proposed `skill-discovery-and-use` shape. | [arxiv.org/html/2602.12670](https://arxiv.org/html/2602.12670v1) |
| **AppWorld** (ACL'24) | 457 APIs, 750 tasks, fully reproducible env, state-based eval. Validates the state-based-verification approach for tool tasks. | [appworld.dev](https://appworld.dev/) |
| **BFCL v4** | Berkeley function-calling leaderboard; multi-turn agentic since v3. Useful tool-selection reference. | [gorilla.cs.berkeley.edu](https://gorilla.cs.berkeley.edu/leaderboard.html) |

### Memory-specific benchmarks worth citing

| Benchmark | What it tests |
|---|---|
| **LongMemEval** | Six dimensions: single-session user recall, single-session assistant recall, **single-session preference recall**, **knowledge update**, **temporal reasoning**, multi-session recall. ICLR'25. |
| **LoCoMo** | Single-hop, multi-hop, open-domain, temporal — 32 sessions / ~600 turns / ~16k tokens. |
| **Mem0** | Five-axis cost-aware scoring (BLEU + F1 + judge + **tokens/query** + **latency**); explicitly penalizes single-axis optimization. |
| **Zep** (DMR + LongMemEval) | Surfaces big gaps: +48% temporal reasoning, +77% preference recall, **−9% single-session assistant recall** — memory systems can hurt simple cases. We should probe for this regression. |
| **MEM2ACTBENCH** | Proactive memory → tool use: does the agent invoke memory at the right moment, select the right tool, ground parameters from recalled facts. Direct precedent for our `true-multi-turn-memory-write` shape's proactivity scoring. |
| **MemoryArena / AMA-Bench** | Interleaves memory writes with downstream decisions across sessions. |
| **Decision-centric rate-distortion** (arxiv 2605.10870) | Scores memory by the *decision-quality loss* compression induces. Principled way to compare recall vs hindsight vs honcho beyond raw recall accuracy. |

### Methodology patterns to adopt (and what changes in this spec)

1. **`pass^k` reliability runs.** Run each task instance **k=5–8 times per harness**;
   report the fraction of tasks that succeed on *every* trial. Reliability is a
   harness-signal property — model temperature variance is identical across both
   harnesses, so it cancels out. **Action:** Track A acceptance criterion now
   requires per-task pass^5 reporting in addition to aggregate score.
2. **Difficulty stratification.** AHE shows component effects flip sign by tier
   (memory helps Hard, hurts Easy). **Action:** every task instance gets a
   `difficulty: easy|medium|hard` tag; sweep reports per-tier and aggregate.
3. **State-based eval over transcript matching** wherever possible. Already
   doing this for code-editing tasks (pytest exit code, file end-state). Extend
   to memory shapes: query the memory backend directly post-run for ground-truth
   facts written, not LLM-judge inspection of the transcript.
4. **Cost-aware reporting.** Already shipping (tokens + $); keep it visible in
   the comparison grid. A harness that wins by 2pp at 10× cost is losing.
5. **Cross-run memory contamination.** **Critical confound we hadn't called
   out.** If recall / hindsight / honcho aren't wiped between trials,
   harness-A's state pollutes harness-B's runs and biases later trials within a
   harness too. **Action:** snapshot+restore (or wipe) the per-agent group on
   recall, the per-bank on hindsight, and the per-workspace on honcho **between
   every trial**.
6. **Different-family judge.** [arxiv 2502.01534](https://arxiv.org/abs/2502.01534)
   shows judge-model-family bias when judge and agent share a model family.
   **We're already safe**: agent = deepseek-v4-pro, judge = claude-opus-4-7
   (different family). Document this explicitly in the spec so future
   model-swap doesn't accidentally introduce leakage.
7. **AGENTS.md cargo-cult warning.** ETH Zurich finding cited by humanlayer:
   agent-generated AGENTS.md files *hurt* performance and cost 20%+ more tokens.
   **Action:** the rich-harness `workspace/AGENTS.md` files
   ([`harnesses/openclaw/workspace/AGENTS.md`](../harnesses/openclaw/workspace/AGENTS.md))
   are human-authored — keep them that way; don't let either harness self-generate.

### Shape validation (which proposed shapes have published precedent)

| Our shape | Published precedent |
|---|---|
| `true-multi-turn-memory-write` | LongMemEval multi-session recall + knowledge update; AMA-Bench; MEM2ACTBENCH proactivity scoring |
| `tool-sprawl-precision` | humanlayer.dev result: Claude Code **82% with curated skills vs 9% without** — bigger effect than we expected; this shape is well-validated |
| `failure-recovery-loop` | τ²-bench dual-control variant; AHE middleware ablation |
| `plan-then-revise` | τ-bench policy-violation tasks (planning layer must catch before tool invocation) |
| `skill-discovery-and-use` | **SkillsBench** three-condition protocol (no-skill / with-skill / self-gen) — adopt this directly |
| `sub-agent-parallel-decompose` | No clean public precedent for delegation *scoring* — humanlayer treats prescriptively, no rubric. **Opportunity for novel contribution.** |
| `context-fill-and-compact` | ContextEcho finding: compaction does NOT reliably correct persona drift across 23 models — we should explicitly score post-compaction persona drift too |
| `live-research-with-memory` | MEM2ACTBENCH ground-truth proactivity scoring |

### Anti-patterns the literature flags (to avoid in our suite)

- **Single-trial scoring** — a 90% pass@1 agent collapses to 57% pass^8. Without
  pass^k we can't tell reliability differences from model temperature noise.
- **Gold-like answer bias** ([ai21.com](https://www.ai21.com/blog/gold-like-answers-benchmarks/)):
  LLM judges favor clean/minimal outputs over messy-but-correct ones. State-based
  eval avoids this; for shapes that must use a judge, calibrate the rubric
  explicitly.
- **Tool-list bloat without measurement.** Loading every available tool inflates
  cost and confuses selection. Either restrict by task or use progressive
  disclosure — but measure both harnesses under identical conditions.
- **Aggregating across difficulty tiers** masks sign-flipping component effects
  (AHE).
- **Cross-run memory contamination** (re-stated — it's the single biggest
  uncalled-out confound in our current setup).

### Novel-contribution opportunities we should claim

The literature has no good public benchmark for:

1. **Write-proactivity scoring** (when *should* the agent write to memory, not
   just whether it can). MEM2ACTBENCH is the closest but small and recent.
2. **Sub-agent delegation quality scoring rubric** — humanlayer is prescriptive,
   no published rubric exists.
3. **Skill-discovery latency** (how many turns before the harness finds and
   invokes the right skill) — SkillsBench scores success but not efficiency.
4. **Cost-equalized multi-harness leaderboards** — HAL provides cost data but
   doesn't equalize.

Three of these (1, 2, 3) directly map to our `true-multi-turn-memory-write`,
`sub-agent-parallel-decompose`, and `skill-discovery-and-use` shapes — so the
harbor-tasks suite has a credible novel-contribution story, not just a
borrowed-methodology story.

## Open questions

- Track A weights are operator judgment, not empirical. Once a Track A sweep
  runs, we can refit weights against observed score variance (down-weight
  categories that produced no split, up-weight ones that did).
- Should `code-editing` be capped at fewer tasks for Track A (e.g. 2 of the 8)
  instead of low-weighting all 8? Same total contribution, less compute.
- The browser/CDP work (task #54) blocks shape #8. Does the methodology stand
  up without shape #8 in the first round? Probably yes — shapes 1–7 cover all
  eight rubric criteria.
- **Cross-harness fairness — honcho asymmetry** (operator decision 2026-05-30,
  task #72): hermes uses honcho natively via `memory.provider: honcho`;
  openclaw does NOT. honcho-mcp upstream ships only as a Cloudflare Worker,
  and openclaw has no native memory-provider plugin point. Operator opted to
  drop honcho on openclaw rather than force-fit. **Published Track A results
  MUST disclose this asymmetry** — it affects categories where honcho's
  dialectic API would pull weight (conversation-persona, research-rag,
  insights-research). Both harnesses still share recall + hindsight. Revisit
  if and when openclaw grows a memory-provider point.

## Revision history

- 2026-05-30 initial draft (operator-requested after context compact + recall
  hindsight-parity ship).
- 2026-05-30 (same day) — Harbor-alignment audit added (`Harbor alignment`
  section). Verdict: almost every spec requirement maps to a native Harbor
  primitive (`n_attempts` for pass^k, `steps/` for multi-turn, `TrialEvent`
  hooks for memory wipe, `MetricType.UV_SCRIPT` for weighted aggregation,
  `[metadata]` for difficulty tags, trajectory.json for tool-call inspection).
  Only **two small Python files** are net-new code; neither touches Harbor
  source. Tracks A/B = two YAMLs, not a framework concept.
- 2026-05-30 (same day) — folded in research subagent findings. Added
  Literature section (HAL, τ-bench, AHE, SkillsBench, LongMemEval, Mem0, Zep,
  MEM2ACTBENCH). Added 4 acceptance criteria derived from literature: pass^k
  reliability runs, difficulty stratification tags, per-trial memory snapshot+
  restore, judge-family-separation note. **Major addition:** cross-run memory
  contamination called out as a previously-unaddressed confound. Confirmed our
  proposed shapes have published precedent (LongMemEval, humanlayer
  82%-vs-9%, τ²-bench, SkillsBench, MEM2ACTBENCH) and that three of them have
  novel-contribution potential (write-proactivity scoring, sub-agent
  delegation rubric, skill-discovery latency).
