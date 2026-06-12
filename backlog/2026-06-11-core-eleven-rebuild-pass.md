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
  can never touch a prod bank (`<prod-group>`/`<prod-group>`/`<prod-group>`).
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

1. Rebuild `harbor-agents-rich:latest` on <run-host> after all Dockerfile/baked
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
<run-host>'s Docker + `.venv` + Infisical creds and cost real money; baton's
pipeline forbids builds/sweeps, so the operator runs D7 after baton merges the
reviewed branch. Acceptance criteria 2 (T9 budget), 3 (T5 oracle), 4 (T3
symmetry), 5 (T4 tokens), and 7 (the grid) are inherently run-dependent and are
verified in D7, not by baton.

---

## Implementation log / as-built (2026-06-11)

Branch `baton/2026-06-11-core-eleven-rebuild-pass` off
`remediation/core-eleven-2026-06-10` (merge-base `bcc1e7b`). 21 files changed,
+1485/-198. Commits: `3415407` (red tests) → `b080bca`/`f05c0d7`/`7d556c6`
(green). All offline-verifiable acceptance is implemented; everything that
inherently needs a build or a live sweep is staged for D7 and explicitly marked
below. **The D7 manual gate (rebuild, oracle 11/11, n=5 re-grid, RESULTS.md) has
NOT been run — it is out of scope for this pipeline.**

### What actually changed (files + essence)

- **T6 — `tasks/ops-debugging/failure-recovery-loop-01/`** (D1). The
  world-readable shell `dfetch` is replaced by a **compiled, stripped C binary**
  built in `environment/Dockerfile` from an inline `.c` + a build-time 32-byte
  random secret (`head -c32 /dev/urandom`), embedded XOR-masked (`0x5a`) into the
  binary; the `.c` and secret header are `rm`'d in the **same RUN layer** so no
  plaintext secret survives any image layer. Success mints
  `NONCE = HMAC-SHA256(secret, "region|token|counter")` (self-contained SHA-256 +
  HMAC in C, no openssl dep). A hidden `dfetch --verify <msg> <nonce>` subcommand
  lets the grader authenticate **without ever holding the secret**. Each rejected
  call appends its stage to an append-only ordered log
  `/var/log/dfetch.progression` (`bad-region → 401 → stale-lock → release`).
  `tests/test.sh` now requires: status=success **AND** `--verify` passes **AND**
  the progression log is present, canonically ordered, and contains `release`,
  **AND** `calls >= MIN_CALLS` (2). IDEAL re-derived to **3** (clean conf-first
  recovery), CEIL kept at 18. `task.toml` description + `solution/solve.sh`
  comment updated.
- **T9 — `tasks/skill-agent-authoring/sub-agent-parallel-decompose-01/`** (D2).
  `environment/Dockerfile` gains a **throwaway first build stage** (`AS calbuild`)
  that compiles a stripped `cal-lookup` C binary with the `CAL-NN → offset` table
  baked in as a **non-string `int` array** (so `strings` reveals nothing), then
  `COPY --from=calbuild` installs only the binary into the agent image — the
  plaintext `registry.json` never reaches a final-image layer. The binary
  `sleep`s `LOOKUP_LATENCY_SEC` (default **8s**, an authoring estimate) per call
  to create real serial-vs-fan-out pressure. `solution/gen.py` now writes the
  registry **twice from one RNG draw**: the answer-key copy to `tests/registry.json`
  and a byte-identical served copy to `environment/registry.json` (both committed).
- **T5 — `tasks/context-rot/context-rot-02/`** (D3). `environment/gen_reports.py`
  replaces every real-world bridge entity/attribute with **invented** ones
  (Lyon→Mournholt, Jackfield→Penhollow, Thames→Mereveil, Saint Luke→Saint Dunmore,
  Durham→Wessenshire, Hereford→Calderwick, Loughborough→Bellforge, Latvia→Vendreth)
  and adds a `DISTRACTORS` table — one **same-type confusable** per chain (a 2nd
  architect, 2nd pottery, 2nd foundry…) placed at a different section depth than
  the graded needle. The answer key is **committed and regenerated in lock-step**:
  `steps/19-recall/solution/solve.sh` and `tests/reward.py` PATTERNS updated to the
  new fictional second-hops.
- **T3 — `hooks/seed_stale_memory.py` (new) + `tools/run_track_a.sh`** (D4). A new
  `TrialEvent.START` hook writes the stale `cache_ttl_seconds=45` memory into the
  trial's `eval-<harness>` hindsight bank, **scoped by `TASK_MATCH` substring** to
  the T3 trial only, reusing `HINDSIGHT_BASE` / `_assert_eval_scope` / `_resolve_group`
  from `wipe_memory_state.py` so it can never touch a prod bank. Registered in the
  driver **after** the wipe hook (order matters; the bare CLI can't load hooks).
- **T4 — no code change** (D5). Per open-question 4 default, `gen_reports.py` is
  left unchanged; the token re-measurement and any fill extension are deferred to
  D7. (T4 = the context-fill overflow task; no file in this diff.)
- **T10 — `tasks/skill-agent-authoring/skill-discovery-and-use-01/`** (D6). The 3
  near-miss skills and all **9 far-decoy skills** now (a) compute their **real
  advertised output** from the CSV arg (a behavioral probe can't collapse the
  candidate set on a constant) and (b) drop a per-skill `.skill-runs/<name>.log`
  breadcrumb. `tests/reward.py` adds `_is_brute_sweep()` — if ≥6 decoy logs each
  cover ≥6 distinct files (a "run all 13 on all 8" sweep), discovery credit is
  **denied**.
- **T11 — `tasks/real-world-workflows/update-record-with-cleanup-01/`** (D6,
  grader-only, no rebuild). `tests/grade.py`: preserve + collateral credit is now
  gated on `dedup_gate = min(1, dedup_ok)` (do-nothing falls **below** 0.50);
  the dedup/preserve identity key drops the **notes** field (`row[:5]`); header
  detection only skips row 0 when its first cell is literally `date` (fixes the
  headerless first-row eat). `task.toml` description corrected (month is **given**
  in instruction.md, not discovered; do-nothing no longer floors at 0.50).
- **Tests (new, red-first):** `tests/exploits/test_t6_progression.py`,
  `test_t9_dockerfile_serves_lookup.py`, `test_t9_registry_equality.py`,
  `test_t10_sweep_no_credit.py`, `tests/regrade/test_t11_floor_notes_headerless.py`.

### Key decisions / deviations from the plan

- **T6 binary-swap defense (beyond the plan).** The plan delegated auth to the
  binary's `--verify`, but a root agent on the shared filesystem could overwrite
  `/usr/local/bin/dfetch` with an `exit 0` stub that "verifies" any nonce. Added a
  **sha256 integrity pin**: the Dockerfile prints the genuine binary's digest and
  writes it to `/usr/local/share/dfetch.sha256`; the grader holds
  `EXPECTED_DFETCH_SHA` and fails closed unless `sha256sum` matches, invoking
  dfetch by **absolute path**. **Action required in D7:** the digest is
  randomised per build, so `EXPECTED_DFETCH_SHA` in `tests/test.sh` is still the
  sentinel `PASTE_DFETCH_SHA256_AT_BUILD_D7` — it MUST be pasted from the build
  log after the rebuild or T6 fails closed for everyone.
- **T9 latency is an estimate, not a calibration.** `LOOKUP_LATENCY_SEC=8` is the
  authoring guess; the plan's "derive from a measured serial baseline" (acceptance
  2) is genuinely run-dependent and stays for D7. The serving mechanism (compiled
  binary) is final.
- **T4 left untouched** by design (open-question 4 default).

### Resolution of the planner's open questions

1. **T6 root-agent residual — ACCEPTED as documented, with an added pin.** The
   "no secret FILE on the fs" property is *proven* (source + header deleted in the
   build layer; agent uid can't read the secret). The `strings`/disassemble
   residual on the stripped binary is acknowledged in code comments as the design
   bet (honest error-walk strictly shorter than reversing HMAC out of a stripped
   binary). A separate verifier image (substrate, out of scope) was NOT pursued;
   instead the binary-swap hole that delegation opened was closed with the sha256
   pin. No substrate touched.
2. **T9 compiled-binary over sleeping http.server — CONFIRMED.** Implemented as a
   compiled on-demand `cal-lookup` (the lower-risk option: single-tasks have no
   `setup.sh` and the rich image has no service entrypoint to boot an http.server).
   The agent-readable `registry.json` never lands in a final layer (built in a
   throwaway stage, copied as a stripped binary only), so the parser-bypass /
   resurrected-registry lesson from the predecessor is respected.
3. **T3 seeding schema + scope — schema is BEST-EFFORT, scope is ENFORCED.** The
   POST body (`{"content": <NL fact>, "metadata": {...value...}}` to
   `…/banks/<bank>/memories`) is the offline best guess; the wipe hook only
   exercised DELETE, so the exact create shape **must be confirmed against the
   live hindsight API in D7** (flagged in the hook docstring). The hook is firmly
   **scoped**: it no-ops unless `TASK_MATCH` ("multistep-stale-memory-vs-file-01")
   is in the task name, and `_assert_eval_scope` guarantees it can only write an
   `eval-*` bank.
4. **T4 baton-side scope — DEFERRED (default taken).** `gen_reports.py` left
   unchanged; the measurement and any fill extension happen in D7.
5. **T5 answer-key ownership — COMMITTED and regenerated in lock-step.** The key
   is the committed `solve.sh` + reward `PATTERNS`; both were regenerated together
   with the corpus in this change, so there is no served/answer-key drift. (T9
   applies the same discipline: served `environment/registry.json` ==
   answer-key `tests/registry.json`, one RNG draw, enforced by
   `test_t9_registry_equality.py`.)

### Lessons / gotchas for the next maintainer

- **Per-build secret ⇒ per-build grader edit.** T6's `EXPECTED_DFETCH_SHA` and
  the broader "digest printed in build log" pattern mean the rebuild is not
  idempotent for the grader — D7 must paste the digest or T6 silently fails
  closed (bin_ok=0 → reward 0 for everyone, looking exactly like a hard task).
- **Answer-key-equivalent files must die in the build stage, not the final
  image.** Both T6 (secret) and T9 (`registry.json`) rely on deleting the
  plaintext in the **same layer / a throwaway stage** — a `rm` in a later layer
  still leaves it recoverable in image history.
- **Hook ordering is load-bearing.** `seed_stale_memory` MUST be registered after
  `wipe_memory_state` or the wipe deletes the seed. The bare `harbor run` CLI
  loads neither — only the driver does.
- **T3 symmetry is the one thing unprovable offline** (acceptance 1b): both
  harnesses retrieving `45` pre-flip needs the live backend and is a D7 gate.

### How to verify

- **Offline (what baton can prove, all green):** on <run-host>,
  `~/benchmarking/harbor/.venv/bin/python -m pytest tests/exploits tests/regrade -q`
  → **37 passed** (run 2026-06-11). These cover the T6 ordered-progression gate,
  the T9 served-lookup + registry-equality invariants, the T10 brute-sweep denial,
  and the T11 floor/notes/headerless fixes.
- **D7 (manual, NOT run here — the operator's gate):** rebuild
  `harbor-agents-rich:latest`; **paste the T6 dfetch sha256 into
  `EXPECTED_DFETCH_SHA`**; oracle 11/11 = 1.0; confirm the live hindsight create
  schema (T3) and that both harnesses retrieve `45` pre-flip; measure the T9
  serial baseline and tune `LOOKUP_LATENCY_SEC`/budget; measure the T4 threaded
  token count; run the severity-gated n=5 re-grid and record Δ + the lifted
  BLOCKED status (tasks 3/5/6/9) in RESULTS.md. "Good" = oracle 1.0, offline suite
  green, and a fan-out run clears more T9 problems than a serial walk within budget.

### D7 progress — rebuild + oracle gate (2026-06-12)

Operator ran the **rebuild + oracle** half of D7 (the n=5 sweep is deferred —
the paid step).

- **Rich image rebuilt** (`harbor-agents-rich:latest`): cached — correct, since
  every change was to a *task* Dockerfile, not the base; the oracle's
  `force_build=true` rebuilds each task image from the unchanged base.
- **T6 pin bug found by the oracle and fixed.** The first oracle run scored
  failure-recovery-loop-01 at **0.0** (`bin_ok=0`): the Dockerfile generated the
  embedded HMAC secret from `/dev/urandom`, so the dfetch binary — and its
  sha256 — changed on every build, and the committed `EXPECTED_DFETCH_SHA` pin
  could never hold across a `force_build`. Pasting any single build's hash would
  have passed once and then silently zeroed T6 for every harness on the next
  rebuild. **Fix (commit on this branch):** fixed eval-internal secret +
  reproducible compile (`-fno-ident`, `-Wl,--build-id=none`,
  `SOURCE_DATE_EPOCH=0`); verified byte-identical across two `--no-cache` builds;
  pinned sha `b524585f…ac932`. In-container security is unchanged (the agent only
  ever sees the stripped binary; `verify_ok` via the pinned genuine binary stays
  the non-forgeable gate). **Re-pin only if the base toolchain changes.**
- **Oracle 11/11 = 1.0, 0 errors** after the fix.
- **Offline suite: 55 passed** (grew from 37 as the rebuild-pass tests landed).

Still gated on the paid n=5 sweep (and only it can prove): T3 seeding symmetry
(acceptance 1b), T9 budget calibration (serial must fail / fan-out must fit), T4
threaded token count, and the lifted BLOCKED status for tasks 3/5/6/9.
