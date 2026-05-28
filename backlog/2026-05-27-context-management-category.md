# Context-management category — long-session behavior tests

- **Date:** 2026-05-27
- **Status:** DEFERRED (to second sweep, after the 17 first-sweep shapes land)
- **Origin:** Operator — "test what happens on a long-running session when you exceed the context window: does it get dumber, compact, or window out important context?"

## Problem

How a harness behaves when the conversation outgrows the model's context
window is one of the most decision-relevant differences between harnesses, and
none of the first-sweep categories test it. When context fills, harnesses do
one of: hard-error, silently truncate (answers degrade with no signal),
auto-compact (lossy summary), hierarchically compact (durable scratchpad), or
externalize-and-retrieve (notes to memory). These are observable in the
trajectory and worth scoring directly.

## Scope

**In:** a new `context-management` category with shapes:

- `long-session-needle` — unique fact established early, ~50 fill turns, recall
  at the end. Verifier: exact match on the secret.
- `long-session-running-state` — maintain a counter/list across many turns.
- `long-session-decision-chain` — an early constraint must still hold very late.
- `compaction-survival` — force compaction, then ask about summarized content.
- `graceful-failure` — push past the limit; did the harness tell the user or
  silently fail?

**Out (for now):** execution. This sweep is expensive (~$0.60/trial of fill
content at a 200K-context model; ~$36 for a full 3-harness × 4-shape × 5-attempt
category). Lock the design; run when budget is approved.

## Design decisions

- **Multi-axis scoring beyond correctness:**
  - `survived` — trial completed without harness-level error
  - `context_managed` — trajectory shows explicit action (compact event, window
    note, memory write) vs silent degradation
  - `final_recall` — graded late-turn retrieval accuracy
  - `degradation_evidence` — judge-scored: did quality visibly drop before failure
- **Force the harness to manage context**, not just the model — fill the window
  via many turns so the harness's own strategy (compact/window/externalize) is
  what's under test.

## Acceptance criteria

- [ ] Shapes authored as Harbor multi-step tasks (`steps/` layout, sandbox
      state persists across turns).
- [ ] Verifiers emit the multi-axis rewards above.
- [ ] A run distinguishes at least two harness context-management strategies
      from the trajectories.

## Open questions

- Pinned-host context limits: the chosen OpenRouter upstream may cap context
  below the model's max. Confirm the pinned host's `context_length` supports
  the fill target before authoring.

## Follow-up tickets

- Depends on [[2026-05-27-task-suite-design]] first-sweep landing.
