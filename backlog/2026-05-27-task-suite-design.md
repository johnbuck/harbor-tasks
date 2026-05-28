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

## Status notes

- 1 of 17 first-sweep shapes authored (fix-bug-with-failing-test-01).
- Remaining 16 shapes + their instances are the bulk of the open work.

## Follow-up tickets

- [[2026-05-27-context-management-category]] — an 18th category (long-session),
  deferred to a second sweep.
