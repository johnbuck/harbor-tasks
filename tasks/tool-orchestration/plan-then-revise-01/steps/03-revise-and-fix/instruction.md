Read `/app/REVISION.md` — the spec changed.

Update `/app/calc.py` (and `/app/PLAN.md`) to satisfy the NEW requirements.
This is the final step and the only one that counts toward the score.

Your work is graded on **each revised requirement independently** (partial
credit per requirement), across three dimensions:

1. **Functional correctness** of the four required functions (`add`,
   `multiply`, `subtract`, `apply_op`) and the `OP_NAMES` constant.
2. **Cleanup of the scrapped plan** — `divide` / `compose` must NOT remain in
   `/app/calc.py`.
3. **Re-planning** — `/app/PLAN.md` must be updated to reflect the revised
   spec (mentions `subtract` + `apply_op`, no longer lists `divide` /
   `compose`).

This step tests whether the harness re-plans cleanly based on the new
requirements vs. blindly executing the original 4-function plan. Each stale
artifact left behind shaves off reward.
