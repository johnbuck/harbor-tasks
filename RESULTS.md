# Harbor-tasks comparison grid — openclaw vs. hermes

> **Role (2026-06-03, `backlog/2026-06-03-results-verdict-thin-over-report.md`).**
> This file is the **thin verdict + validation-state layer**, not the numbers source.
> Per-trial metrics are owned by Harbor's reporting (`harbor view`, per-job
> `result.json`) + `metrics/track_a_weighted.py` → `track_a_report.json`. RESULTS.md
> owns only what no automated report can: the **validation state**, the plain-English
> **verdict**, the **construct-validity caveats**, and how to reproduce.

**Same model both harnesses:** `deepseek/deepseek-v4-pro` (openclaw via the `xrouter`
custom provider, hermes via OpenRouter), reasoning ON, both pinned to one OpenRouter
upstream (`novita`). Any gap is the **harness**, not the model or load-balancer luck.

---

## Validation ladder — where the suite actually stands (2026-06-24)

A task is only as trustworthy as the highest tier it has *passed*. Each tier proves
something the one below cannot. **No task is `approved=true` yet** — approval requires
Tier 2 (Track-B) or Tier 2 + Tier 4 (Track-A).

| Tier | What it proves | Status (full active suite: 32 eval tasks = 11 core + 21 non-core) |
|---|---|---|
| **1. Offline grader/regression tests** | Grader *logic* scores correct strings up, dump/hedge/bypass strings down — on **synthetic** inputs | ✅ **244 pass** (`pytest tests/`) |
| **2. Oracle** | Each task **builds** and its **reference `solve.sh`** scores 1.0 — happy path + plumbing | ✅ **31/31 oracle-able = 1.0** (`configs/oracle-full.yaml`). `browser-find-fact-01` (gates on `browser_used`) and `prod-behavioral/conversational-01` (needs a real agent) are **not oracle-able by design** |
| **3. Real-agent n=1 e2e smoke** | The **actual harness** runs every task; rough separation + which tasks break live | ✅ **complete** (`configs/smoke-n1.yaml`, both harnesses) — see below. **n=1 is a smoke, not a verdict** |
| **4. n≥3 `pass^k` verdict** | Reliability spread; Track-A tasks genuinely discriminate | ❌ **not run for the current (reworked) tasks.** The 2026-06-10 n=5 (Δ=0.188) is **superseded** — it predates the second-adversarial-pass + rebuild + non-core remediation that reworked these tasks |

### Tier 3 — n=1 e2e smoke results (indicative, NOT banked)

Both harnesses ran all 32 tasks e2e. **The suite separates them, in both directions**
— the key construct-validity signal (a one-sided result would suggest a confound):

- **openclaw led:** failure-recovery, context-fill-01/02/03, proactive-preference,
  update-record-with-cleanup, plan-then-revise, pr-diff-review.
- **hermes led:** browser-find-fact, memory-conversational, stale-memory-vs-file.
- **both aced (1.0/1.0):** context-rot-01/02, factual-lookup-cited, pandas-sql,
  prompt-injection-resistance, refactor-multi-file, shell-pipeline, skill-discovery,
  unit-tests.

**Caveats (why these numbers are not the verdict):**
1. **n=1 is a coin-toss.** A 1.0-vs-0.0 at one sample is not a reliability result;
   that is precisely what Tier 4 (`pass^k`, n≥3) measures. Numbers are not banked.
2. **~6 tasks scored ~0 on BOTH harnesses — pending transcript triage** (free, no
   re-run): `true-multi-turn-memory-write`, `find-contradictions`, `secret-scan`,
   `tool-sprawl-precision`, `agentic-research-with-memory`, and
   `sub-agent-parallel-decompose`. Each is one of: a grader too strict for a real
   agent's phrasing (a false-zero only visible e2e), genuine difficulty, or an infra
   gap. **`sub-agent-parallel-decompose` is an expected zero** — its in-container
   latency-gated lookup (T9) is rebuild-deferred and was never built, so a real agent
   cannot solve it in-container (see `backlog/2026-06-11-core-eleven-rebuild-pass.md`).
3. Harbor truncates long trial-dir names; a couple of multistep rows are ambiguous in
   raw dumps (data is intact, naming collides).

---

## Methodology — the discrimination is *reliability + efficiency*, not single-run pass

Both harnesses are competent and both have memory, so on binary pass/fail tasks they
often *both pass* → BLUNT. The harness difference shows up as:

1. **Graded scoring is mandatory** — a binary verifier scores both 0/1 and stays
   blunt; the *fraction* reveals the gradient. (All active tasks are graded.)
2. **Reliability variance (the core signal):** the same memory/recovery tasks flip
   between runs — one harness sometimes aces and sometimes fails. A single run is a
   coin-toss; only **`pass^k` (n≥3)** measures "hermes passes 3/5 where openclaw
   passes 5/5." This is the τ-bench reliability result and is why Tier 4 is the verdict.
3. **Efficiency** (robust every run): equal-result cost / tool-call counts on the same
   model are a pure harness signal.

---

## Memory substrate (symmetric — disclosed)

Both harnesses run **hindsight-only**, so any memory Δ is the harness's *use* of the
same backend, not a backend asymmetry:

- **recall (Graphiti/neo4j):** removed from both harnesses 2026-06-03; its wipe path
  was removed from `hooks/wipe_memory_state.py` on 2026-06-24 (it was firing every
  trial and failing on an unresolvable host).
- **honcho:** DISABLED 2026-06-10 (`honcho.json "enabled": false`) so hermes matches
  openclaw's hindsight-only surface. (Running honcho+hindsight vs hindsight-only made
  any memory Δ uninterpretable.)
- **built-in file memory** (MEMORY.md/USER.md): off for the eval.
- **Anti-contamination:** `hooks/wipe_memory_state.py` wipes the eval hindsight bank
  (+ honcho, a no-op while disabled) before every trial, scoped to `eval-*` only
  (guarded — can never touch a production memory group). T3 stale-memory seeding is a
  paired `seed_stale_memory` hook fired after the wipe.

---

## Approval state

**0 / 33 active eval tasks are `approved=true`.** The suite is now **35 dirs under
`tasks/`** — 33 active eval tasks (11 core + 21 non-core + 1 prod-behavioral MVP) + 2
`_verify` fixtures; the 20 former deprecated tasks were **archived to `archive/`**
(commit `196f2b0`). The 32 build-able eval tasks pass Tiers 1–2 (and ran Tier 3), but
approval is gated on Tier 4 for Track-A and is held pending the both-zero triage. The
task catalog reads NEEDS REVIEW until each task clears its gate.

## How to reproduce

```bash
# Source your Infisical identity env first (see AGENTS.md "Running a sweep").
# Tier 2 — full-suite oracle (free, no LLM): builds every task + runs solve.sh
OPENROUTER_API_KEY=oracle-noop harbor run -c configs/oracle-full.yaml
# Tier 3 — n=1 e2e smoke (real agents, both harnesses): rough separation
CONFIG=$PWD/configs/smoke-n1.yaml N_ATTEMPTS=1 JOB_NAME=smoke-n1 tools/run_track_a.sh
# Tier 4 — the verdict-bearing grid (the paid run; the actual harness verdict)
CONFIG=$PWD/configs/core-suite.yaml N_ATTEMPTS=5 JOB_NAME=core-suite-n5 tools/run_track_a.sh
```

Each sweep emits TWO jobs — `<job_name>__openclaw` and `<job_name>__hermes` — so each
job's rollup is a single harness. Results land in `jobs/` (gitignored). Browse:
`harbor view jobs --port 8089 --host 0.0.0.0`.

## Revision history

- 2026-05-30 initial template. 2026-05-31 INTERIM (smoke + sharpening n=1).
- 2026-06-10 n=5 core-eleven grid (Δ=0.188) — **superseded 2026-06-24** (tasks
  reworked by the second-adversarial-pass + rebuild + non-core remediation since).
- 2026-06-24 restructured around the validation ladder; recorded the full-suite oracle
  (31/31) + the n=1 e2e smoke (bidirectional separation, ~6 both-zero pending triage);
  corrected the substrate (recall removed, honcho disabled → hindsight-only) and the
  approval state (0 approved; Tier 4 still owed for the current tasks).
