# Harbor-tasks comparison grid — openclaw vs. hermes

**Status (2026-05-31):** INTERIM — the instrument is **proven to discriminate
harness from model** on three axes (efficiency, memory reliability, recovery
reliability); the final **n=5 pass^k** grid is pending a budget decision (the
sharpened tasks turned out token-heavy, so a focused n=5 ≈ $60). Numbers below
are from the **n=1 smoke (94 tasks)** + the **focused n=1 (17 sharpened/
discriminating tasks)** + a single-task memory validation. n=1 reward is NOISY
by design — the discrimination lives in pass^k reliability, which n=1 cannot
capture (see Key Finding below). Treat single-run rewards as directional.

**Same model both harnesses:** `deepseek/deepseek-v4-pro` (openclaw via the
`xrouter` custom provider, hermes via OpenRouter), reasoning ON. Any gap is the
harness, not the model.

---

## KEY FINDING — the discrimination is *reliability*, not single-run success

Both harnesses are competent and both have memory, so on binary pass/fail tasks
they usually *both pass* → BLUNT. The harness difference shows up as:

1. **Efficiency** (robust, every run): openclaw spends **0.35–0.62× hermes's
   cost** for equal results. Same model ⇒ this is a pure harness signal. Hidden
   example: on `tool-sprawl` both scored reward 1.0, but openclaw made **3 tool
   calls vs hermes's 7**.
2. **Reliability variance**: the *same* memory/recovery tasks flip between runs —
   hermes *sometimes* aces them and *sometimes* fails; openclaw is steady:

   | task | run A | run B |
   |---|---|---|
   | `memory-conversational-01` | oc 6/6, **he 3/6** (Δ0.50) | both 6/6 (tie) |
   | `memory-conversational-03` | both tie | oc 6/6, **he 3/6** (Δ0.50) |
   | `failure-recovery-loop-01` | oc reward 1.0 (4 retries), **he 0.0 (51 retries)** | both 1.0 |

   That flip *is the signal*. A single run is a coin-toss; **pass^k (n≥3)** is the
   only thing that measures "hermes passes 3/5 where openclaw passes 5/5." This is
   exactly the τ-bench reliability result and is why n=5 is the real grid.

**Proven discriminator (clean single-task validation, fixed wipe hook):**
`multistep-memory-conversational-01` → openclaw **6/6 facts**, hermes **3/6**,
**Δ=0.50**, near-identical cost. openclaw's recall+hindsight out-retrieved
hermes's honcho+recall under load.

> **⚠️ Baseline VOID after 2026-06-03 (commit `597070b`).** The `recall` MCP was
> erroring on every hermes invocation and has been **removed from both eval
> harnesses** — the memory substrate is now **openclaw = hindsight only** vs
> **hermes = honcho + hindsight**. This Δ=0.50 was measured on the old
> recall-bearing substrate, so it no longer holds; the core-suite n=1 run
> re-establishes the memory baselines on the new substrate.

---

## Smoke baseline (94 tasks, n=1, pre-sharpening)

- **36 / 45 comparable tasks BLUNT** (both harnesses ace at 1.0) — confirms the
  pre-sharpening suite was model-dominated, as the spec predicted.
- Overall weighted reward Δ ≈ **+0.04** (openclaw), **below** the 10% bar on
  single-run reward — but efficiency Δ and the reliability flips are large.
- Real discriminators found: `failure-recovery-loop` (retry efficiency),
  `find-contradictions` (precision), and the memory tasks.

## Sharpening pass (all 15 high-weight BLUNT tasks → graded)

The fix for bluntness: **graded scoring is mandatory** (a binary all-or-nothing
verifier scores both harnesses 0 and stays BLUNT; the *fraction* reveals the
gradient) + a category-appropriate stressor. See the spec's "Sharpening
playbook." All 15 oracle-validate (oracle→1.0, partial→fractional), `FROM
harbor-agents-rich`, difficulty=hard:

| Category (weight) | Tasks | Stressor |
|---|---|---|
| conversation-persona (2.0) | -01, -03 | 8 facts / 4 distractors / graded 6-fact recall |
| context-management (3.0) | fill-01/02/03 | chunks **deleted pre-recall** (cheat-proof), graded 14-item recall from memory |
| tool-orchestration (3.0) | sprawl, plan-revise | 57 decoys + F1; graded re-plan /8 |
| skill-agent-authoring (3.0) | sub-agent ×2, skill-discovery | 10-file /40, 20-file /60, decoy-discovery /16 |
| real-world-workflows (3.0) | schedule, update, prompt-injection | counter-proposal state /14, 30-row /19, 4-injection /4 |
| insights + research-rag (2.0) | contradictions, cited-lookup | 8 contradictions /8, 8 cited facts /8 |

Focused n=1 on the sharpened set confirmed graded scoring works and **caught a
schema bug** (6 verifiers emitted nested-dict rewards → Harbor `ValidationError`;
fixed, see FOOTGUNS #38). `memory-conversational-03` hit Δ=0.50; the rest need
n=5 to surface their reliability gap.

---

## Headline (Track A) — PENDING n=5

| Metric | openclaw | hermes | Δ |
|---|---:|---:|---:|
| Weighted aggregate (pass@1) | *n=5 pending* | *n=5 pending* | — |
| Weighted aggregate (pass^5) | *n=5 pending* | *n=5 pending* | — |
| **Cost ratio (oc/he), equal results** | **0.35–0.62×** | 1.0× | **openclaw ~40–65% cheaper** |
| Memory recall under load (best clean run) | 6/6 | 3/6 | **+0.50** |

## Open questions for the n=5 run

- Does `context-management` discriminate, or do both memory backends ace it?
  (Both got 14/14 at n=1 — need to confirm the chunk-deletion gate fired and
  whether it's genuine recall or both-are-good.)
- pass^5 reliability spread on the memory + recovery tasks (the core signal).
- Whether `prompt-injection` (both perfect) is a permanent tie (model-level
  safety) → candidate to drop from Track A weighting.

## Known asymmetries (disclosed)

- **Honcho**: hermes uses honcho as a native memory provider; openclaw does not
  (operator decision, task #72). Both share **hindsight**. `recall` was shared
  too until 2026-06-03 (commit `597070b`), when it was dropped from both
  harnesses for erroring on every hermes call — so the current memory substrate
  is openclaw=hindsight vs hermes=honcho+hindsight (the <memory-host> recall server at
  :8408 is untouched; the harnesses just no longer mount it).
- **Anti-contamination**: `hooks/wipe_memory_state.py` wipes the eval recall
  group / hindsight bank / honcho workspace before every trial — scoped to
  `eval-*` only (guarded; can never touch prod `<prod-group>/<prod-group>/<prod-group>`). honcho 409 +
  hindsight 405 wipe bugs fixed 2026-05-31 (FOOTGUNS #37).

## How to reproduce

```bash
source ~/.config/infisical/infisical-identity.env
# Full Track A (weighted + pass^k), persistent jobs dir:
N_ATTEMPTS=5 tools/run_track_a.sh
# Focused discrimination set (the sharpened + proven-discriminating tasks):
CONFIG=$PWD/configs/track-a-focused.yaml N_ATTEMPTS=5 JOB_NAME=track-a-focused-n5 tools/run_track_a.sh
```

**One job per harness:** each run emits TWO jobs — `<job_name>__openclaw` and
`<job_name>__hermes` — so each job's dashboard rollup is a single harness's
scores and the two compare directly (don't mix both agents in one job; that
forces per-task comparison and defeats the rollup). The weighted report reads
both dirs and computes the split.

Results land in `jobs/` (persistent, gitignored). Browse them:
`harbor view jobs --port 8089 --host 0.0.0.0` → http://LAN-IP:8089
(use the dashboard's compare view across the two `__openclaw` / `__hermes` jobs).

## Revision history

- 2026-05-30 initial template (before any sweep).
- 2026-05-31 INTERIM: smoke + sharpening + focused n=1 findings; instrument
  proven on efficiency + reliability axes; n=5 pass^k pending budget decision.
