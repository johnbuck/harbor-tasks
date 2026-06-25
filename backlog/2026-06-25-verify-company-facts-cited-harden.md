---
status: PROPOSED
epic: E4
date: 2026-06-25
---

# Harden `verify-company-facts-cited` — it's too easy (both harnesses scored 1.0)

**Epic:** E4 — Task Suite (validity)
**Status:** PROPOSED — small difficulty bump, fold into the unify per-task pass.
**Origin:** noncore-remediation triage (`2026-06-16-noncore-task-remediation.md`,
the "still open" list). In the 2026-06-22 n=1 smoke this task scored **1.0 for
both hermes and openclaw** — saturated/blunt, so it can't separate the harnesses.
(n=1 is a coin toss, but a clean 1.0/1.0 is a strong easy signal.) Its sibling
`audit-report-contradictions` is NOT in scope here — that one only looked broken
because it crashed on the DNS outage and never ran; it just needs a re-run.

## The problem

The task (`research-rag/verify-company-facts-cited`) asks 10 factual questions about
a fictional company (Halcyon Systems, served locally), each needing the CURRENT
value AND a citation to the AUTHORITATIVE page. Today each fact has exactly ONE
archived near-duplicate decoy, and the authoritative-vs-archive distinction is
**guessable from the URL path** (`/archive/`, `team-2018`, `2019-profile`,
`deprecated v1`). So an agent can pick the right page by filename heuristic, never
reasoning about authority — hence the saturation.

## How to make it harder (no corpus balloon, no long-context — just confusability)

1. **Hide the path tell.** Put at least one superseded value on a page that *looks*
   current (e.g. a stale homepage/section not obviously under `/archive/`), so the
   agent must use content/recency/authority signals, not the filename.
2. **Two decoys per fact, not one.** Add a second plausible-but-wrong source per
   fact (third-party press mention, mirror/cache, changelog entry) carrying a
   *different* wrong value, so it's a 1-of-3 discrimination.
3. **A few cross-page facts.** Make 2–3 answers require reconciling a correction
   noted on a *different* page (the current value isn't stated outright anywhere —
   it's "old value, minus the restatement on page X"), so single-page lookup fails.
4. **Stricter citation.** Require the exact authoritative page (ideally section /
   anchor); citing an archive/mirror scores 0 even when its value coincidentally
   matches. Keep the grader format-robust (S2) and crash-guarded (S4) as-is.

Keep all of this MECHANICAL and OUT of the instruction — no telegraphing which
pages are decoys.

## Decision gate (unify)

Keep-and-harden vs cut is a **unify** call (`2026-06-25-unify-full-suite.md`, one
bar: valid + graded + ungameable; per-task discrimination not required). If kept,
do the 4 fixes above, then re-confirm with an oracle (=1.0) and the next n-run.
If the suite already has enough citation-discipline coverage, cutting is also fine.
