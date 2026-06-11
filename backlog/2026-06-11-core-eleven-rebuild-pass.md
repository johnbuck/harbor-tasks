---
status: APPROVED
epic: E4
date: 2026-06-11
---

# Core-eleven rebuild pass — land the deferred image/run-dependent fixes

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-11
**Status:** APPROVED 2026-06-11 — direct continuation of
`2026-06-11-core-eleven-second-adversarial-pass.md`, which landed every
offline-verifiable fix (merged `7c670d8`, 37/37 offline checks green) and
explicitly deferred everything needing a Docker rebuild, a live sweep, or
external-memory-backend wiring to this pass.
**Origin / triggered-by:** the second-adversarial-pass as-built log, "Open
questions — as-built resolution" items 1, 2, 4, 5 + acceptance criteria 1b, 6,
7, all tagged REBUILD/RUN-DEFERRED.
**Predecessor:** `2026-06-11-core-eleven-second-adversarial-pass.md` (the
offline pass; read its as-built section first — it is the source of truth for
what each deferred fix still needs).

## Problem

Four of the suite's critical fixes are only half-done: the offline pass changed
the graders and generators but the load-bearing half lives in the Docker image
or in a live backend, which baton's offline pipeline cannot build or run. Until
this pass lands, **tasks 3, 5, 6, 9 are BLOCKED for any verdict-bearing n=5
run** (per the predecessor's design decision 3 / open question 5):

- **T6** still trusts the agent-writable `/var/log/dfetch.state`. The offline
  `calls >= 4` gate kills the *demonstrated* `calls=0` forgery, but the agent
  runs as **root** (`environment/Dockerfile:24`), so forge-with-4-junk-calls
  still scores. Closing it needs a compiled tool with an embedded secret.
- **T9** is currently **unsolvable in-container**: the per-problem calibration
  offset that each answer now depends on is served only from a verifier-side
  `tests/registry.json`. The in-container latency-gated lookup that should
  serve `CAL-NN → offset` does not exist yet, and the budget that should force
  fan-out over serial is uncalibrated.
- **T5**'s "multi-hop" is still single-hop with real-world parametric bridges —
  the offline pass added the S1 wipe + S3 exclusivity but deferred the
  fictionalize-bridges + same-type-distractor corpus rebuild.
- **T3** has no mechanical stale-memory seeding, so a memoryless harness still
  reads the live file cold and scores 1.0 indistinguishably from verification
  discipline (predecessor T3 #3 / acceptance 1b).
- **T4**'s overflow claim is still unverified against a real threaded-trial
  token count.

## Scope

**In:** the five REBUILD/RUN-DEFERRED items below (T6, T9, T5, T3, T4), the
`harbor-agents-rich` image rebuild they require, and the post-rebuild
validation gate (oracle 11/11 + the severity-gated n=5 re-grid). Plus the two
MINOR tasks the offline pass skipped, folded in opportunistically **because the
image is being rebuilt anyway**: **T10** (decoy-logging — a Dockerfile change)
and **T11** (floor-gating / second-step — grader-only, no rebuild).

**Out:** the substrate/adapters/provider-pin (untouched); re-litigating any
offline fix already merged; the scratch-discipline spin-off task (its own
future spec, per the predecessor's Follow-up tickets); RESULTS.md numbers until
the sweep actually runs.

## Design decisions / per-item plan

Each item names the exact deferred design the predecessor already committed to
in code comments — implement that, do not re-design.

### D1 — T6 compiled `dfetch` + HMAC nonce + grader recompute

The `test.sh` header already specifies the target. Implement it:
- Replace the world-readable shell `dfetch` (`environment/Dockerfile:28-85`)
  with a **compiled** helper (a small C binary, or a PyInstaller/`shc` build —
  C is cleanest) that embeds a **build-time secret** baked into the image and
  **stripped from any agent-readable path** before the agent starts.
- Success nonce = `HMAC(secret, region|token|counter)` — deterministic given
  the secret, unforgeable without it.
- The tool writes an **ordered error-progression log** (append-only) recording
  each rejected call's error stage (bad-region → 401 → stale-lock → release).
- The grader **recomputes** the expected nonce from the same secret (read from
  a verifier-only path, never `/var/log/dfetch.state`) and **requires the
  ordered progression** in the log — so a `STATUS=success` state with no real
  recovery, at any call count, scores 0.
- Re-derive `IDEAL` from the true oracle path once the progression is
  mandatory; keep `CEIL=18`.
- **Secret handling:** the build-time secret is an eval-internal value, not a
  user secret — bake it as a Docker build ARG or a file `chmod 700` root-owned
  and `rm`'d from agent-reachable layers; it never appears on a command line or
  in `.env` (hard rule 7). Verify the agent cannot read it (`find / -name … `
  from the agent uid returns nothing) as part of acceptance.

### D2 — T9 in-container latency-gated registry lookup + budget calibration

`gen.py` already emits `registry.json` (`CAL-NN → offset`) and folds the offset
into each answer; the prose names only the code. Add the serving half:
- Bake an **in-container, localhost-only** lookup that serves `CAL-NN → offset`
  with **real per-request latency** (a sleeping `http.server` on `127.0.0.1`,
  or a `dfetch`-style file-read wrapper that `sleep`s). **Never external
  internet** despite `allow_internet=true`. The registry it serves is generated
  alongside the problems (move the generation so the *served* table and the
  *answer-key* table come from one RNG draw — the served copy lives in
  `environment/`, the answer-key copy stays in `tests/`; they must match).
- **Budget calibration:** set the wall-clock budget so a measured
  honest-serial walk (60 problems × per-lookup latency) **cannot** finish but a
  fan-out run can. Derive the latency × budget from a measured serial baseline,
  not a guess — record the measurement in the as-built log.
- Keep the offline parser-regression check green (it already proves a
  prose-only parser collapses to chance).

### D3 — T5 fictionalize bridges + same-type distractors

In `environment/gen_reports.py`:
- Replace all real-world bridge pairings (Maw & Co→Jackfield,
  Whitefriars→Thames, Frosterley→County Durham, Taylor→Loughborough,
  Riga→Latvia, etc.) with **fictional** attributes so parametric knowledge /
  web lookup cannot shortcut a hop.
- Seed **same-type confusable distractors** in the filler (a second named
  architect, a second pottery, a second foundry…) so the anchor hop genuinely
  disambiguates — the bridge sentence alone must no longer be type-unique.
- Re-verify the rot-curve buckets and the oracle still trace 1.0 against the
  regenerated corpus.

### D4 — T3 mechanical stale-memory seeding (mirror the wipe hook)

The stale value must reach BOTH harnesses' memory backends identically:
- Add a seeding step that mirrors `hooks/wipe_memory_state.py` in reverse —
  **write** `cache_ttl_seconds=45` into the trial's `eval-<harness>` hindsight
  bank (the substrate is hindsight-only + symmetric post the 2026-06-10
  rework), reusing `HINDSIGHT_URL` and the same `_assert_eval_scope` guard so it
  can never touch a prod bank (`juliet`/`yui`/`akane`).
- Wire it into `tools/run_track_a.sh` as a `TrialEvent` hook (or a step-00
  pre-step) that fires **after** the wipe — the bare `harbor run` CLI does not
  load hooks (same footgun the wipe hook documents), so the driver is the only
  correct injection point.
- **Symmetry is verifiable only live** (acceptance 1b): after seeding, both
  harnesses must retrieve `45` when asked, *before* the file flips to `275`.
  This is the one item that cannot be proven offline — gate it on the sweep.

### D5 — T4 token re-measurement

Run a real threaded trial and measure the actual cumulative token count
(`gen_reports.py` currently yields ~728K est., under the 1M window). If
under-window, extend the fill (add weeks — note the ~230-line headroom to the
1700-line read cap) until overflow is real, then correct the task.toml claim
with the **measured** number, not an estimate.

### D6 — T10/T11 (opportunistic)

- **T10** (rebuild): make the decoy skills **log their invocations** too (so a
  brute-force "run all 13" sweep is detectable) and gate discovery credit on
  not-sweeping; make the 9 far-decoy stubs **actually compute** their advertised
  output so a behavioral probe can't collapse the candidate set.
- **T11** (no rebuild): gate the preserve/collateral credit on evidence of
  action (`min(1, dedup_ok)`) so do-nothing no longer floors at 0.50; exclude
  notes from the record-identity key; fix the headerless-output first-row eat;
  align the `/19`→`/16` and "discover the month" description drift.

### D7 — Rebuild + validation gate (the whole point of this pass)

1. Rebuild `harbor-agents-rich:latest` on thringle after all Dockerfile/baked
   changes (D1, D2, D6-T10).
2. **Oracle 11/11 = 1.0** (Docker build + schema + plumbing, no LLM cost) —
   catches TOML/heredoc/schema breakage before paying for a sweep.
3. Run the offline regression suite (37+ checks) green against the rebuilt tree.
4. **Severity-gated n=5 re-grid** of the core suite; record the new Δ in
   RESULTS.md with the caveat that fixing fake signal may legitimately *lower*
   the predecessor's Δ 0.188 — what matters is the remaining Δ being
   attack-clean.

## Acceptance criteria

1. **T6:** forge-with-N-junk-calls scores 0 — a `STATUS=success` state without
   the ordered error-progression log fails at any call count; the agent uid
   cannot read the build-time secret; oracle still 1.0; IDEAL re-derived from
   the real oracle path.
2. **T9:** the in-container `CAL-NN` lookup serves offsets with real latency on
   localhost only; a measured honest-serial run **cannot** finish in budget
   while a fan-out run **can** (numbers recorded); offline parser-regression
   still ≤ chance; served registry == answer-key registry.
3. **T5:** no bridge pairing is answerable from parametric/web knowledge (all
   fictional); every bridge question has ≥1 same-type distractor in filler;
   oracle 1.0 on the regenerated corpus.
4. **T3 (acceptance 1b):** after the seeding hook, both harnesses retrieve `45`
   pre-flip in a live trial; the seeding refuses any non-`eval-` scope; the
   weight-0 stale/hallucination diagnostics still emit.
5. **T4:** the task.toml overflow claim matches a **measured** threaded-trial
   token count; if it was under-window, the fill was extended until overflow is
   real.
6. **T10/T11:** T10 brute-force sweep no longer earns full discovery and far
   decoys compute real output; T11 do-nothing floor is below 0.50 and the
   denominators/descriptions are accurate.
7. **Gate:** image rebuilt; **oracle 11/11 = 1.0**; offline suite green; n=5
   re-grid run and its Δ + the lifted BLOCKED status (tasks 3/5/6/9) recorded
   in RESULTS.md.

## Execution note (baton + manual split)

D1–D6 are **code** (Dockerfiles, `gen.py`, a C helper, a seeding hook, grader
recompute logic, offline tests proving each) and go through baton like the
offline pass. **D7 is manual** — the Docker rebuild, oracle, and n=5 sweep need
thringle's Docker + `.venv` + Infisical creds and cost real money; baton's
pipeline forbids builds/sweeps, so the operator runs D7 after baton merges the
reviewed branch. Acceptance criteria 2 (T9 budget), 3 (T5 oracle), 4 (T3
symmetry), 5 (T4 tokens), and 7 (the grid) are inherently run-dependent and are
verified in D7, not by baton.
