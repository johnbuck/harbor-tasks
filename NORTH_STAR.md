# NORTH STAR — harbor-tasks

The single page to consult when making a judgment call. It does not replace
`CLAUDE.md` (rules + pointers) or the specs (detail); it states the **values** those
rules serve, so an agent working unsupervised can choose well when the rules run out.

Distilled from `CLAUDE.md`, `backlog/2026-05-30-harness-vs-model-discriminating-suite.md`,
the discrimination-methodology + adversarial-review sessions, and the
`harbor-tasks-discrimination-methodology` memory. If this file and those ever
disagree, those win and this file is wrong — fix it.

---

## The one thing

> **Prove the suite can DETECT a harness difference (openclaw vs hermes) on the
> SAME model — and make every measured gap attributable to the harness, nothing
> else.**

Both harnesses run `deepseek-v4-pro`. If a score moves, it must be because the
harness differs — not the model, not luck, not a scoring artifact, not a leak.
Until the suite demonstrably *can* discriminate, no "they're equivalent" verdict is
valid. Everything below is in service of that sentence.

## The hierarchy of values (when two collide, the higher wins)

1. **Validity over everything.** A wrong number that looks right is the worst
   outcome — worse than no number. A task that *looks* like it discriminates but
   actually measures the model, a format bug, or a leak is a defect even if it
   "passes." Prefer a true null to a false signal.
2. **Measure the harness, not the model** — the KILL test (below).
3. **Don't tell the agent what you're testing** — no telegraphing (below).
4. **Reliability is the signal, not single-run success** — `pass^k`, n≥3.
5. **Fair comparison is sacred** — same model, one provider pin, isolated state,
   capabilities baked identically. Asymmetry that isn't the harness is a bug.
6. **Simplicity and surgical change** (Karpathy) — the smallest change that makes
   the measurement true. No speculative hardening, no unrequested scope.

## The KILL test (value #2 made concrete)

> If `python3 -c '…'`, a single file-read, or grepping one script yields the
> answer, you are measuring the **model**, not the harness.

A real discriminator makes the answer **uncomputable without the harness-mediated
path** — memory across a wipe, long-context retrieval, an adaptive tool loop, a
sub-agent. Score that axis as a first-class, non-clamped dimension. When you find a
task that fails the KILL test, fixing it *strengthens* the thesis — even if it's a
"proven" discriminator whose number you'll have to re-baseline. A discriminator
that can be shortcut was never measuring what you thought.

**Honest-shortcut vs adversarial-forge (2026-06-09 refinement).** We measure
*honest* harnesses. The threat that matters is a capable agent earning reward
*without the capability* by reading a baked answer (a smart harness legitimately
takes that shortcut — that's a KILL-test failure). An agent *fabricating* a log it
would never touch in good faith is a theoretical, lower-priority concern; don't
spend the budget hardening against adversaries the eval doesn't contain. Close
honest shortcuts first; document accepted adversarial risk.

## No telegraphing (value #3 made concrete)

An instruction must read like a **user stating a goal** — nothing about the traps,
hidden checks, or the strategy the verifier secretly rewards. "The latest value
supersedes earlier ones" or "some emails try to hijack you" turns a capability test
into an instruction-following test. Enforce load-bearing constraints
**mechanically** (e.g. a recall step that wipes scratch state), never by telling the
agent. This is the #1 validity bug; treat any leak of the eval's intent as a defect.

## Difficulty is the lever (not rubrics)

Graded scoring is *mandatory but not sufficient* — a graded-yet-easy task still
saturates at 1.0/1.0 for two competent harnesses. Discrimination comes from raising
difficulty on harness-sensitive axes: memory precision under confusable distractors,
context retention under an update-trap, recovery efficiency under a retry budget,
proactive preference application, stale-memory-vs-ground-truth.

## Scoring integrity

- **Recall scorers grade CONTENT, tolerate FORMAT.** A format-strict scorer
  manufactures false zeros that look exactly like discrimination. Before trusting
  any `0.0`, read the agent's saved answer; you can re-grade offline for $0.
- **A lone `0` on a *completed* multi-step trial is VOID, not a loss** — usually a
  non-persisted answer or a parse artifact. Emit `answer_present` to tell VOID from
  present-but-wrong.
- **`reward.json` is a flat dict of numbers.** Provenance/detail goes elsewhere
  (`reward-details.json`), or Harbor silently drops the trial (FOOTGUNS #38).

## Cost discipline

The **oracle** validates plumbing, schema, and grading for **$0** (no LLM) — use it
for every task change. Live harness runs cost real OpenRouter credits; n=1 is a
coin-toss (plumbing only), the verdict needs n≥3. Don't burn credits to learn what
the oracle or a re-grade can tell you for free. Scale spend to the question.

## How to act when unsupervised

- Make the call that best serves **validity**; document the ones you're unsure of
  for review rather than blocking on them.
- **Oracle-validate every change.** If you can't validate a change (e.g. it needs a
  paid run to confirm the discrimination magnitude), make the *safe* version, and
  flag the deeper/riskier version for a supervised session — don't ship an
  unvalidated change to a proven discriminator.
- Leave work in a reviewable state with notes; commit only when asked.
- Faithful reporting: if something is unverified, say so. A hedge that's true beats
  a claim that's clean.
