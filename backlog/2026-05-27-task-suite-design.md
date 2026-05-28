# Task suite design — categories, shapes, first-sweep selection

- **Date:** 2026-05-27
- **Status:** IN PROGRESS
- **Origin:** Operator — "we need to define the tasks we want to use."

## Problem

A harness comparison is only as good as its tasks. A task is worth running
only if its result would change a real decision. We need a task suite that
reflects the operator's actual workloads, with enough instances per shape that
a winner reflects real difference, not random variance (the signal-vs-noise
point: few tasks per category make luck look like a harness gap).

## Scope

**In:** the operator-confirmed inventory below — 17 categories, 67 task
*shapes*. Each shape becomes ~5 task *instances* (e.g. 5 different bugs for
`fix-bug-with-failing-test`). First sweep = 1 shape per category (17 shapes ×
~5 instances = ~85 task instances).

**Out:** authoring all 67 shapes up front. Breadth-first (1 shape/category)
validates the full pipeline; depth comes after.

## The inventory (67 shapes / 17 categories)

- **Code editing (3):** fix-bug-with-failing-test, add-feature-with-tests, refactor-multi-file
- **Ops / debugging (6):** diagnose-from-logs, shell-pipeline, triage-incident, read-SQL-logs, adversarial-code-review, adversarial-spec-review
- **Research / RAG (5):** factual-lookup-cited, multi-source-synthesis, topic-deepdive, market-research, market-insight
- **Conversation / persona (4):** stay-in-character, remember-facts, handle-topic-shifts, refuse-out-of-guardrail
- **Building prototypes (3):** mcp-server, webapp-spike, cli-tool
- **Building designs (4):** sys-arch-diagram, db-schema, api-contract, ui-wireframe
- **Insights research (3):** outlier-detection, pattern-extraction, find-contradictions
- **Marketing (4):** email-copy, social-variants, brief, ad-creative
- **Data analytics (4):** pandas-sql-from-nl, data-cleaning, visualization, spreadsheet-formula
- **Documentation (4):** api-docs-from-code, runbook, readme, adr
- **Code / spec review (4):** pr-diff-review, design-doc-review, pattern-conformance, missing-test-detection
- **Test authoring (4):** unit-tests, integration-tests, regression-test-from-bug, property-based-tests
- **Tool orchestration (4):** multi-tool-plan-execute, mcp-chaining, shell-web-file-pipeline, tool-selection
- **Skill / agent authoring (3):** skill-md, sub-agent, slash-command
- **Migration (4):** schema-migration, framework-upgrade, dep-bump-breaking, legacy-modernization
- **Compliance / security (4):** secret-scan, injection-xss, policy-pii, iac-misconfig
- **Backup / DR (4):** backup-restorability, restore-runbook, coverage-gap, rto-rpo

First-sweep shape per category + verifier types are in [`SHAPES.md`](../SHAPES.md).

## Design decisions

- **Shapes vs instances.** A shape is a task archetype; an instance is one
  concrete realization. ≥5 instances/shape so a per-cell score is meaningful.
- **Breadth-first first sweep.** One shape per category proves every workload
  end-to-end before going deep.
- **Multi-axis rewards per task** (correctness + instruction_following +
  tool_selection + goal_adherence + solution_quality) — see SHAPES.md.
- **Verifier per category:** pytest for objective code/data tasks, LLM-judge
  rubric for the rest, mixed where both apply.

## Acceptance criteria

- [ ] All 17 first-sweep shapes authored (Harbor task dirs), ~5 instances each.
- [ ] `harbor run -c configs/<sweep>.yaml` runs the full first sweep across the
      target harnesses and produces a populated `/compare` grid.
- [x] First worked example shipped + validated:
      `tasks/code-editing/fix-bug-with-failing-test-01` (1.0 on both harnesses).

## Status notes (updated 2026-05-27 PM)

**Authored so far — all under `tasks/code-editing/`, 3 shapes:**

- `fix-bug-with-failing-test` × 5 (01 wordcount, 02 running_total,
  03 palindrome, 04 intervals, 05 flatten) — easy→medium.
- `add-feature-with-tests` × 2 (01 LRU cache /medium, 02 infix evaluator /hard).
- `refactor-multi-file` × 1 (01 geometry pkg, forces polymorphic refactor /hard).

All 8 validate with `--agent oracle` (8/8 correctness 1.0).

**Sweep results:**

- `sweep-coding-5` (5 fix-bug × openclaw+hermes, Kimi K2.6 pinned Io Net):
  10/10 correct. openclaw 166.8s/$0.219, hermes 179.8s/$0.211 — effectively
  tied. Finding: `fix-bug-with-failing-test` is **too easy to differentiate**
  these harnesses; the single-task "hermes 35% faster" was n=1 noise (washed
  out across 5).
- `sweep-coding-8` (adds the 3 harder tasks): **LAUNCHED, results pending**
  (background job `b0i1rs36u`, log `/tmp/sweep.log`, results
  `/tmp/harbor-jobs/sweep-coding-8/`). Open question this sweep answers: do the
  harder shapes finally split openclaw vs hermes?

**Remaining:** the other 14 first-sweep categories (1 shape each) + more
instances per shape. Code-editing is the only category with tasks so far.

## How to run a sweep (operational quickref)

From <dev-host>, model = Kimi K2.6 pinned to Io Net (privacy-allowed, deterministic):

```bash
cd /tmp/harbor   # the Harbor checkout with uv env + bun-built viewer
set -a; source ~/.config/infisical/infisical-identity.env; set +a
TOKEN=$(infisical login --method=universal-auth \
  --client-id="$INFISICAL_CLIENT_ID" --client-secret="$INFISICAL_CLIENT_SECRET" \
  --domain="$INFISICAL_SITE_URL/api" --plain --silent)
PYTHONPATH=<repo> infisical run \
  --projectId=INFISICAL_PROJECT_ID --env=production --path=/proxy/ \
  --domain="$INFISICAL_SITE_URL" --token="$TOKEN" \
  -- uv run harbor run -c <repo>/configs/first-real-trial.yaml \
       --job-name <NAME> --n-concurrent 3 -y
```

- Config (`configs/first-real-trial.yaml`) points its dataset at
  `tasks/code-editing/` (picks up ALL task dirs there) — narrow it or add a
  per-sweep config to target a subset.
- Validate new tasks free with `--agent oracle` before spending tokens.
- View: `harbor view /tmp/harbor-jobs --port 8089` (needs bun; already built).
- Per-task breakdown: the analysis one-liner used in chat reads each trial's
  `result.json` → `agent_info.name`, `agent_result.{cost_usd,n_*_tokens}`,
  `agent_execution.{started_at,finished_at}`, `verifier_result.rewards`.

## Follow-up tickets

- [[2026-05-27-context-management-category]] — an 18th category (long-session),
  deferred to a second sweep.
