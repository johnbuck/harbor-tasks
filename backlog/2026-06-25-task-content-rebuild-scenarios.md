---
status: PROPOSED
epic: E4
date: 2026-06-25
---

# Rebuild task CONTENT into believable real-world scenarios — without losing the measurement

**Epic:** E4 — Task Suite (validity + legibility)
**Date:** 2026-06-25
**Status:** PROPOSED — self-contained hand-off for another session / the baton
pipeline. Execute one task per run, oracle-gated.
**Origin:** operator. The suite is now legible by NAME (all 33 renamed, commit
`7550dfa`) but several tasks' CONTENT is still synthetic filler ("PROJECT VEGA —
18 weekly reports", "60 opaquely-named tools", "WESTMARCH PRIORY inspection
records") that reads like nonsense to a human. This spec rebuilds that content
into scenarios a real user would plausibly hand an agent — **while preserving,
exactly, each task's power to discriminate the harness.** The operator's
constraint, verbatim: *"make sure that we're not losing the material goodness of
the tests."*

---

## North Star

Every active task is a scenario a real user would plausibly ask an agent to do,
with a plain instruction a human can read end-to-end — **and it still measures the
exact same harness capability, at the same difficulty, with the same scoring, as
it did before the rewrite.** Legibility is added; discrimination is not subtracted.

## The cardinal rule: re-skin the SCENARIO, preserve the SKELETON

Every task is two separable layers. The rebuild changes ONLY the first:

- **SKIN (rewrite freely):** the surface narrative + fixture *content* — the story,
  the prose, the entity names, the document theme. This is what makes it read like
  "PROJECT VEGA" vs "a long email thread about a product launch." Make it believable.
- **SKELETON (preserve EXACTLY — this is the "material goodness"):** the
  discriminating *mechanism* and the *scorer*. Specifically:
  1. **The hidden mechanic** that makes the answer uncomputable without the harness:
     the `setup.sh` scratch-wipe, the silent mid-task file rewrite, the
     value-stripped-from-disk-but-stated-in-conversation, the context-window
     OVERFLOW (token budget), the latency gate. Same structure, same step count,
     same trigger points.
  2. **The scorer:** the exact reward dimensions, their weights, the penalty logic,
     the gates, and the weight-0 diagnostics. A rebuild may re-point the grader at
     new fixtures but MUST NOT change the dimension set, the weights, or the
     pass/fail thresholds.
  3. **Kill-test resistance:** a bare `python3 -c` / single file-read still cannot
     solve it. The new scenario must not accidentally make the answer computable.
  4. **No telegraphing:** the instruction reads like a user stating a goal — it
     must not leak the trap, the hidden check, or the required strategy.
  5. **Mechanical enforcement:** the load-bearing constraint stays enforced by
     `setup.sh`/the environment, never by instruction text.

**If a change touches the skeleton, it is out of scope for this spec** — that is a
re-design, not a re-skin, and needs its own difficulty/validity review.

## Why this is safe when done right

The skeleton's two riskiest pieces — the mechanic and the scorer — can usually be
kept **byte-identical**:
- The mechanic lives in `setup.sh` / step structure / the Dockerfile, which are
  theme-agnostic (a wipe wipes regardless of what story the documents tell). Keep
  them.
- The grader keys on *structure* (N facts, a final-vs-stale comparison, a tool-call
  log) not on the story. Re-point it at the new fixtures; keep its dimensions and
  weights. Where the grader hardcodes fixture values (the "answer key"), regenerate
  those from the new fixtures with the SAME logic.

So the default posture is: **rewrite instruction + fixtures + the fixture-generator;
leave `setup.sh`, the step graph, and the grader's scoring logic alone.**

---

## Scope

**IN — full scenario rebuild (the 15 synthetic / partial tasks):**

| New name (task dir) | was | cluster |
|---|---|---|
| `track-project-across-context-overflow` | multistep-context-fill-01 | long-context |
| `track-final-state-through-corrections` | multistep-context-fill-02 | long-context |
| `separate-two-parallel-projects` | multistep-context-fill-03 | long-context |
| `distinguish-my-facts-from-others` | multistep-memory-conversational-01 | memory |
| `recall-details-across-task-switching` | multistep-memory-conversational-02 | memory |
| `recall-details-under-high-load` | multistep-memory-conversational-03 | memory |
| `apply-standing-preferences-unprompted` | multistep-proactive-preference-01 | memory |
| `refresh-config-over-cached-value` | multistep-stale-memory-vs-file-01 | memory |
| `persist-facts-through-corrections` | true-multi-turn-memory-write-01 | memory |
| `pick-right-shell-utility` | tool-sprawl-precision-01 | tool precision |
| `redesign-module-keep-constraints` | plan-then-revise-01 | control loop |
| `parallel-delegation-under-deadline` | sub-agent-parallel-decompose-01 | delegation |
| `research-org-profile-cited` | agentic-research-with-memory-01 | research |
| `verify-company-facts-cited` | factual-lookup-cited-01 | research |
| `basic-knowledge-qa` | prod-behavioral/conversational-01 | baseline probe |

**AUDIT-ONLY — the 18 already-realistic tasks (Bucket A):** these read believably
already (e.g. `clean-expense-ledger`, `book-meeting-with-contact`,
`security-code-review`, `http-outage-root-cause-from-logs`,
`summarize-support-emails-safely`). For each: confirm the scenario is believable,
lightly polish the instruction for plain language, and **fix the stale `[metadata]
shape`/`tags`/`description`** left over from the rename (the rename changed the dir
but not these fields). **No scenario or grader change.** If an audit finds one is
actually synthetic, promote it to the IN list — don't silently rewrite it.

**OUT:** anything that changes the skeleton (mechanic, scorer dimensions/weights,
difficulty); the 20 archived tasks; renaming (done).

---

## Process per task (the loop — follow in order)

0. **Baseline the oracle.** Run the task's Harbor oracle BEFORE any change; record
   the reward and per-criterion breakdown. This is the regression target.
1. **Write the discriminating contract** (a short block at the top of the rebuild
   PR / as-built): the capability measured, the mechanic, the scorer
   dimensions+weights, the kill-test answer ("why `python3` can't solve it"). This
   is the checklist the rebuild must not violate.
2. **Design the new scenario** (the skin) so it carries the SAME skeleton: same
   number of facts/steps, same overflow token budget, same correction/trap points,
   same tool/decoy counts, same latency. Pick something believable (see briefs).
3. **Rebuild the skin:** instruction.md (plain-language user goal, no telegraphing),
   the fixture *generator* (e.g. `gen_reports.py` → new theme, same structure/size),
   and any fixture files. **Do not touch** `setup.sh`, the step graph, or the wipe.
4. **Re-point the grader, don't redesign it.** Keep the reward dimensions, weights,
   penalties, gates, and weight-0 diagnostics identical. If the grader hardcodes an
   answer key, regenerate it from the new fixtures with the SAME extraction logic.
   Grader must remain **rewardkit** (AGENTS.md hard rule #8) — convert if it was a
   bespoke/pytest holdover (see `2026-06-25-rewardkit-100pct-grader-conversion.md`).
5. **Update `task.toml`:** `description`, `[metadata] shape`, `tags`, `keywords` to
   the new scenario. Keep `difficulty`, `category`, env limits, step timeouts.
6. **Validate (the gates below). Loop until all pass.**

---

## Per-task rebuild briefs

Each brief: **measures** · **SKELETON to preserve (do not change)** · **new SKIN
(believable scenario)** · **realism pitfalls**. Token sizes and counts are part of
the skeleton — keep them.

### Long-context ×3

**`track-project-across-context-overflow`** (was context-fill-01)
- *Measures:* recalling facts that were stated EARLY and then evicted when the
  context window overflows.
- *Skeleton:* 18 documents, ~72K tokens each (~1.3M total — MUST exceed the
  model's ~1M window so eviction is forced); 12 tracked facts, several stated early
  then never repeated; documents deleted by `setup.sh` before the recall step;
  grader = current-value recall over 12, line-anchored, dump-penalised.
- *New skin:* a long **email/Slack thread** or **project changelog** over a quarter
  that a user genuinely accumulated (a product launch, a house renovation, a
  migration) and asks "what's the current state of X?" Keep 18 chunks at the same
  sizes.
- *Pitfalls:* don't shrink the corpus below the window (kills the overflow); don't
  restate the early facts late (kills the eviction trap).

**`track-final-state-through-corrections`** (was context-fill-02)
- *Measures:* reporting the FINAL value of facts that were corrected 2–3× under
  full-window saturation (final vs stale).
- *Skeleton:* 18 docs (~1.3M, overflow); 12 attributes each corrected 2–3× across
  the timeline; one decoy that was never true; grader = `max(0, current_hits −
  stale_hits)/12`, +1 final-value-with-≤1-prior, −1 for the decoy; docs wiped
  pre-recall.
- *New skin:* the same long thread/changelog where decisions visibly CHANGED over
  time (owner reassigned, date slipped, vendor swapped). Believable: "summarise the
  current plan from this thread."
- *Pitfalls:* preserve the exact correction multiplicity (2–3×) and the −1 decoy;
  don't make the final value the most-recently-mentioned by position only (the
  agent must track supersession, not pick the last line).

**`separate-two-parallel-projects`** (was context-fill-03)
- *Measures:* avoiding cross-attribution when two concurrent projects share the same
  field names with different values.
- *Skeleton:* two interleaved projects, shared attribute schema, confusable values
  re-stated across 18 docs; grader credits correct per-project attribution, penalises
  cross-talk; overflow + wipe preserved.
- *New skin:* a person tracking **two clients / two teams / two apartments** in one
  inbox; "what's the status of each?" Keep both projects sharing field names.
- *Pitfalls:* the two projects MUST share field names + plausibly-swappable values —
  that collision IS the test.

### Memory ×6 (state must survive the `setup.sh` scratch-wipe)

**`distinguish-my-facts-from-others`** (was memory-conversational-01)
- *Measures:* precise recall of the user's own facts amid confusable facts about
  other people.
- *Skeleton:* 12 personal facts planted across early turns; 4 distractor turns inject
  *sibling* facts about others (same fields, different values — e.g. someone else's
  allergy/pet/car); step-07 `setup.sh` sources `wipe_scratch.sh` (wipes /tmp,
  /var/tmp, $HOME caches, session stores) AND deletes /app before recall; grader =
  correct/12 with a **sibling penalty** (stating a distractor's value or hedging both
  ≈ 0.33) + a `wipe_assertion` flat-0 guard.
- *New skin:* onboarding a personal assistant — you mention your details over a chat,
  and along the way reference friends/coworkers (whose details are the confusables).
  Already believable; mostly a prose polish + keep the structure.
- *Pitfalls:* the distractors MUST be same-field siblings (a *confusable*), not random
  noise; keep the wipe + the sibling-penalty scorer exactly.

**`recall-details-across-task-switching`** (was memory-conversational-02) and
**`recall-details-under-high-load`** (was memory-conversational-03)
- *Measures:* same precision recall, escalated distractor density (02 = interleaved
  with small unrelated TASKS; 03 = maximum distractor load).
- *Skeleton:* identical to the above (N facts, sibling distractors, step-wipe,
  correct/N + sibling penalty); only the distractor *density* differs (this is the
  difficulty knob — preserve the relative escalation 01 < 02 < 03).
- *New skin:* same assistant relationship; 02 interleaves real small asks ("convert
  this", "summarise that") between the personal facts; 03 packs the most confusables.
- *Pitfalls:* keep 02 and 03 genuinely harder than 01 — the escalation is the point.

**`apply-standing-preferences-unprompted`** (was proactive-preference-01)
- *Measures:* proactively applying standing preferences from memory, unprompted,
  when the immediate request is phrased in the WRONG format.
- *Skeleton:* 4 standing preferences stated **memorise-only** (ISO dates, 24h time,
  no emoji in headings, sign with initials — or equivalents); scratch wiped; the
  final request is deliberately phrased in non-preferred form (a trap — the agent
  must apply prefs from memory, not mirror the prompt); grader = applied/4.
- *New skin:* a user who set up "house style" preferences early, then later asks for
  an announcement/email phrased sloppily; the agent should silently apply the style.
- *Pitfalls:* the final request MUST be mis-formatted (else there's nothing to apply
  proactively); prefs MUST be memorise-only (no file).

**`refresh-config-over-cached-value`** (was stale-memory-vs-file-01)
- *Measures:* re-reading live file state instead of trusting a value cached in
  conversation memory.
- *Skeleton:* the agent reads + repeatedly USES a value early (cementing it in
  memory); a later step's `setup.sh` **silently rewrites the file** (e.g. 45 → 275)
  then deletes itself; the final turn asks for the current value; grader = reward
  1.0 **iff** the current value is reported AND the stale one is NOT (dumping both
  forfeits; an honest "now 275 (was 45)" is carved out).
- *New skin:* a config/feature-flag/price/threshold the user asks about, computes
  with, then it changes under them. Believable as-is; re-skin the entity.
- *Pitfalls:* the rewrite MUST be silent (agent never told); keep the
  exclusive-credit scorer (current AND not stale).

**`persist-facts-through-corrections`** (was true-multi-turn-memory-write-01)
- *Measures:* proactively updating memory when facts are CORRECTED mid-conversation,
  then using the latest values.
- *Skeleton:* 8 facts shared over turns, **two corrected late** (e.g. timezone
  Pacific→Mountain, schedule Tue/Thu→Mon/Wed); scratch wiped; final recap must use
  the corrected values + a downstream task that respects the corrected constraints;
  grader = `(correct_fields/8) × (0.85 + 0.15·downstream_ok)`; stale values score 0.
- *New skin:* you tell an assistant your details, then correct two ("actually I moved
  to Denver", "we changed climbing to Mondays") and ask it to plan around them.
- *Pitfalls:* keep exactly two corrections + the downstream-constraint check; stale =
  0 must hold.

### Tool precision ×1

**`pick-right-shell-utility`** (was tool-sprawl-precision-01)
- *Measures:* tool-selection discipline — picking the right tools among many
  opaquely-named look-alikes by reading their `--help`, not name-matching.
- *Skeleton:* 60 candidate tools; exactly 3 solve the task; their names are OPAQUE
  (function only in `--help`); ~9 name-collision decoys match the task verbs but do
  the wrong thing; **the answer VALUE is deliberately NOT scored** (a script could
  compute it); grader keys on the logged tool invocations: `0.5·selection_F1 +
  0.5·call_efficiency`; computing offline without invoking tools scores 0.
- *New skin:* a realistic **toolbox of 60 similar CLI utilities** (think a data-ops
  bin/ with `sort`, `sort-numeric`, `colsum`, `col-sum`, `tally`, `count-rows`,
  variants) where only 3 give correct results; the 3 facts to extract are believable
  (count valid records, top term, total amount).
- *Pitfalls:* the answer value MUST stay unscored (else it becomes a model test); keep
  the opaque names + collision decoys + the invocation-log grader.

### Control loop ×1

**`redesign-module-keep-constraints`** (was plan-then-revise-01)
- *Measures:* retaining a numeric constraint stated ONLY in earlier conversation
  across a mid-task context regression.
- *Skeleton:* a multi-step coding task where a bound (e.g. clamp `[-1000,1000]`) is
  stated only in the step-1/2 conversation; step-3's `setup.sh` STRIPS the helper +
  the bound from disk AND from the step-3 instruction; the agent must re-apply the
  bound from memory; leaked scratch notes → reward 0.0; grader = `clamp_memory 0.40 +
  functional 0.40 + cleanup 0.12 + replan 0.08`.
- *New skin:* a believable module evolution (a pricing/validation/units library) with
  a safety bound agreed early, then a "drop X, add Y, rename Z" change request that
  omits the bound. Keep add/remove/rename ops.
- *Pitfalls:* the bound MUST appear only in conversation (never in step-3 files); keep
  the 0.40/0.40/0.12/0.08 split and the scratch-leak → 0 gate.

### Delegation ×1

**`parallel-delegation-under-deadline`** (was sub-agent-parallel-decompose-01)
- *Measures:* parallelising via sub-agents to beat a serial time wall.
- *Skeleton:* 60 INDEPENDENT subtasks, each needing a value from a **latency-gated
  binary (≈8 s/call)**; serial = 60×8 s = 480 s, which blows the 600 s agent timeout
  even with instant reasoning; only parallel sub-agent sessions clear enough in time;
  grader = correct/60 (no concurrency bonus — serial simply finishes fewer).
- *New skin:* 60 believable independent mini-jobs (e.g. 60 customer records to enrich,
  each requiring one slow API/lookup), where the lookup is rate-limited. Keep 60 +
  the 8 s gate + the 600 s timeout relationship.
- *Pitfalls:* preserve the latency × count > timeout arithmetic EXACTLY (that wall is
  the whole test); each subtask must stay genuinely independent + non-batchable.

### Research ×2

**`research-org-profile-cited`** (was agentic-research-with-memory-01)
- *Measures:* multi-page synthesis with value + an AUTHORITATIVE citation per fact.
- *Skeleton:* a sandboxed seeded corpus (~16 interlinked pages); 8 facts each needing
  the correct value AND an authoritative citation in the same unit (wrong-value or
  archive-only → 0); grader = matched/8, co-located value+citation.
- *New skin:* "write a cited one-pager on <partner org / vendor> from their site/docs"
  — a believable due-diligence / proposal task. Keep the seeded corpus structure +
  the authoritative-vs-archive distinction.
- *Pitfalls:* keep the citation-must-be-authoritative + co-located grader (this is what
  defeats a guess-from-memory shortcut).

**`verify-company-facts-cited`** (was factual-lookup-cited-01)
- *Measures:* fact retrieval with authoritative-source distinction + stale-page
  resistance.
- *Skeleton:* a seeded KB with current + outdated/archived pages; 10 fact items, each
  scored on correct value + authoritative citation (archived/stale source → 0);
  grader = found/10.
- *New skin:* "answer these 10 questions about <company> with sources" — believable
  analyst/reporter task. Keep the stale-page distractors.
- *Pitfalls:* keep the stale/archived decoy pages — filtering them IS the test.

### Baseline probe ×1

**`basic-knowledge-qa`** (was prod-behavioral/conversational-01)
- *Measures:* baseline factual recall + transcript capture for the production-agent
  eval mode (a SMOKE/floor, not a discriminator).
- *Skeleton:* one factual question; reward 1.0 iff the captured answer names the
  correct fact (e.g. PARIS); `answer_present` weight-0 diagnostic distinguishes VOID
  from wrong.
- *New skin:* keep it a plain, believable one-line factual ask. Minimal change.
- *Pitfalls:* this one's material goodness is intentionally low (it's a baseline) — do
  not over-engineer it into a discriminator; just make the question read naturally.

---

## Hard constraints / gates (every rebuilt task MUST pass)

1. **Oracle-equivalent.** The Harbor oracle reward for the reference `solve.sh` is
   1.0 after the rebuild, and the per-criterion breakdown matches the pre-rebuild
   baseline (same dimensions, same weights). Capture before/after in the as-built.
2. **Scorer unchanged.** Same reward dimensions, weights, penalties, gates, and
   weight-0 diagnostics. If the grader file changed at all, add an offline
   **regrade-matrix test** proving correct / dump / hedge / bypass strings still score
   exactly as before.
3. **Kill-test still fails.** A `python3 -c` / single file-read still cannot produce
   the reward. State the new kill-test answer in the as-built.
4. **No telegraphing.** The instruction reads as a user goal; it does not name the
   trap, the hidden check, or the required strategy. Re-run the telegraphing check
   (`2026-06-01-telegraphing-audit.md`).
5. **Mechanism intact + mechanical.** The wipe / silent-rewrite / strip / overflow /
   latency gate is unchanged and enforced by `setup.sh`/the environment, never by
   instruction. Overflow tasks still exceed the window; latency task still beats the
   timeout only via parallelism.
6. **rewardkit only** (AGENTS.md hard rule #8) — `python3 tools/check_rewardkit.py`
   stays green for the task.
7. **`reward.json` flat dict of numbers** (hard rule #2); provenance →
   `reward-details.json`. **`FROM harbor-agents-rich:latest`** (hard rule #1).
8. **Separation preserved.** Where an n=1 two-harness run is affordable, the rebuilt
   task must NOT saturate to 1.0/1.0 — it should separate at least as well as before.
   (n=1 is a smoke; the banked check is the n≥3 grid.)

## Acceptance criteria

- [ ] All 15 IN tasks rebuilt to believable scenarios; the 18 Bucket-A tasks audited
      + their stale `shape`/`tags`/`description` fixed.
- [ ] For each rebuilt task: discriminating-contract block written; oracle reward +
      breakdown identical to baseline; kill-test answer restated; no-telegraphing
      check passed.
- [ ] `tools/check_rewardkit.py` green; `configs/oracle-full.yaml` oracle 33/33 = 1.0.
- [ ] A human can read every task's instruction + `task.toml` description and
      understand what's asked and (roughly) what it reveals about the harness — with
      zero eval jargon.
- [ ] No skeleton changed: a diff review confirms `setup.sh` / step graph / scorer
      weights are untouched (or equivalence-proven).

## Validation ladder (per task)

1. **Offline:** the grader's regrade-matrix + exploit/bypass tests pass on synthetic
   strings (no Docker). 2. **Oracle:** builds + `solve.sh` → 1.0, breakdown matches
   baseline (run host, Docker, $0). 3. **n=1 e2e** both harnesses: does not saturate.
   4. **n≥3** pass^k: folds into the suite verdict grid (separate, operator-gated).

## Risks → mitigations (how we avoid losing goodness)

- **Re-skin drifts into re-design** → the skeleton-diff gate (criterion 8 above):
  reviewer confirms `setup.sh`/steps/scorer are byte-identical or equivalence-proven.
- **New scenario accidentally makes the answer computable** (kill-test regression) →
  mandatory kill-test restatement + an offline bypass test.
- **Telegraphing creeps in** while making prose "clear" → the no-telegraphing check;
  clarity is about the GOAL, never about the trap.
- **Overflow corpus shrunk for readability** → token-budget assertion in the
  fixture-generator; the corpus must still exceed the window.
- **Grader re-point introduces a false-zero** (FOOTGUNS #2/#38) → keep the S4 crash
  guard + `answer_present`; regrade-matrix test.

## Execution

One task per **baton** run (test-first: write the discriminating-contract + the
regrade-matrix as the red tests, then rebuild to green), oracle-validated on the run
host before merge. Order: do one task per cluster first (context-fill-02,
memory-conversational-01, tool-sprawl, plan-then-revise) to prove the re-skin pattern
end-to-end, then fan out the rest. Bucket-A audits can batch (they're field fixes).
```
