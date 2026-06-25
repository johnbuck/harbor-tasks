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

### Tier 3 — n=1 e2e smoke + both-zero triage (done 2026-06-25)

Both harnesses ran all 32 build-able tasks e2e. The suite separates them in BOTH
directions (openclaw led failure-recovery / context-fill / update-record / plan-revise /
proactive-preference; hermes led browser-find-fact / memory-conversational /
stale-memory; ~8 both-aced at 1.0). **n=1 is a coin-toss, not a verdict — not banked.**

**Both-zero triage** (the 6 tasks that scored ~0 on *both* harnesses):

- **INFRA-VOID — re-run, not a loss:** `find-contradictions` and
  `agentic-research-with-memory` both **crashed on a DNS outage**
  (`EAI_AGAIN openrouter.ai`) — never reached the model. ⚠️ The smoke ran during
  **transient network instability**, so *other* n=1 zeros may also be infra artifacts,
  not real fails — another reason n=1 isn't the verdict.
- **GRADER/FIXTURE BUG — fix (cheap, offline-verifiable):**
  - `true-multi-turn-memory-write` — openclaw recalled all 8 facts and wrote a correct
    answer but scored 0/8: the grader's Part-A/Part-B splitter matches the bare word
    "dinner" in the answer's title heading → discards Part A
    (`steps/08-recall-question/tests/reward.py`, the `pb = next(...'part\s*b|dinner'...)`
    split; plus an unanchored `fish` in the MEAT regex). Fix: anchor the split to a
    heading. (hermes genuinely failed this one — a real signal, keep.)
  - `secret-scan` — the seeded "real" secrets use **canonical example values**
    (`AKIAIOSFODNN7EXAMPLE`, the jwt.io default token, `example.com`) and the
    instruction says NOT to flag placeholders, so both agents correctly reject all four.
    Fixtures contradict ground truth. Fix: reseed with realistic non-canonical fakes.
- **REAL-FAIL / design — no grader fix; judge at n≥3:**
  - `tool-sprawl-precision` (core-eleven) — incentive inversion: openclaw computed
    offline (no tool calls), hermes took decoy bait. Floors both at n=1 (a documented
    design tension); needs n≥3 + possibly the "make offline the longer path" mitigation.
  - `sub-agent-parallel-decompose` (core-eleven) — **correction to an earlier note:**
    the latency-gated `cal-lookup` IS built into the image. Both failed to delegate
    within the 600s budget (hermes timed out, openclaw persisted nothing).
    `LOOKUP_LATENCY_SEC` is an unvalidated estimate — the deferred D7 n≥3 calibration
    ("serial must fail / fan-out must fit") is what's owed.

Net: of the 6, **2 are VOID (infra), 2 are real bugs to fix, 2 need n≥3 to judge.**

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

## Open work (next steps, post-triage 2026-06-25)

1. **Fix 2 false-zeros (cheap, offline):** `true-multi-turn-memory-write` Part-B
   heading-anchor + MEAT-regex fix; `secret-scan` reseed fixtures with realistic
   non-canonical secrets. Add a regression check each, re-run their graders offline.
2. **Re-run the 2 network-VOID tasks** (`find-contradictions`,
   `agentic-research-with-memory`) — verify `openrouter.ai` DNS on the run host first
   (provider-pin rule); ideally re-run the whole n=1 smoke on a stable network since
   the outage may have spuriously zeroed others.
3. **Tier 4 — n≥3 `pass^k` grid on a stable network:** the verdict-bearing run AND the
   calibration the two design tasks (`tool-sprawl-precision`,
   `sub-agent-parallel-decompose`) need.
4. **Flip `approved=true`** per task that then clears its gate (Tier 2 for Track-B;
   Tier 2 + Tier 4 for Track-A).

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
