# Task shapes — first sweep (17 categories × 1 shape)

One canonical shape per category for the first end-to-end sweep. Each
shape will get ~5 task **instances** before we run the comparison.

Verifier column: **pytest** = run a test file, pass/fail; **judge** = LLM-judged
rubric in `reward.json`; **mixed** = pytest for objective parts, judge for
quality.

| # | Category | Shape | Verifier | Multi-turn? |
|---|---|---|---|---|
| 1 | Code editing | `fix-bug-with-failing-test` | pytest | no |
| 2 | Ops / debugging | `diagnose-from-logs` | judge | no |
| 3 | Research / RAG | `factual-lookup-cited` | judge (correctness + citation present) | no |
| 4 | Conversation / persona | `remember-facts` | judge | **yes** (5 turns) |
| 5 | Building prototypes | `cli-tool` | pytest | no |
| 6 | Building designs | `api-contract` | mixed (OpenAPI lint + judge) | no |
| 7 | Insights research | `find-contradictions` | judge | no |
| 8 | Marketing | `email-copy` | judge | no |
| 9 | Data analytics | `pandas-sql-from-nl` | pytest (result equality) | no |
| 10 | Documentation writing | `readme` | judge | no |
| 11 | Code / spec review | `pr-diff-review` | judge (real issues found, no rubber-stamping, no piling on) | no |
| 12 | Test authoring | `unit-tests` | mixed (tests run + judge for coverage quality) | no |
| 13 | Tool orchestration | `tool-selection` | judge (right tool chosen) | no |
| 14 | Skill / agent authoring | `sub-agent` | deterministic rewardkit (correct/60) | no |
| 15 | Migration | `dep-bump-breaking` | pytest (post-migration suite passes) | no |
| 16 | Compliance / security | `secret-scan` | pytest (catches planted secrets, no false positives) | no |
| 17 | Backup / DR | `restore-runbook` | judge | no |

## Reward axes (every task emits these)

Beyond the binary `reward` (correctness), every verifier emits:

- `correctness` — 0/1 or graded — primary axis
- `instruction_following` — 0–1 — did the agent follow stated constraints
- `tool_selection` — 0–1 — did the agent use appropriate tools
- `goal_adherence` — 0–1 — did the agent stay on task
- `solution_quality` — 0–1 — judged quality of the approach

These flow through to `result.json` as separate columns; the `/compare`
view shows each as its own coloured cell.

## After the first sweep

Once the first sweep is run + reviewed, expand by adding:

- More instances per shape (5 → 10 if signal is strong)
- More shapes per category (from the full 67-shape inventory captured in task #36)

The full 67-shape inventory is in task #36 description — pull from there
when expanding.
