# harbor-tasks

Task suite + run configs for evaluating agent harnesses (openclaw, hermes,
aider, openhands, ...) with [Harbor](https://github.com/harbor-framework/harbor)
under controlled conditions.

Designed to answer one question: **which harness is best for the work I
actually do, on the same model, under identical conditions?**

## Structure

```
harbor-tasks/
├── README.md
├── RESULTS.md          # comparison-grid template / final report
├── SHAPES.md           # first-sweep task shapes (one per category)
├── backlog/            # specs (PROPOSED → IN PROGRESS → IMPLEMENTED → done/)
├── configs/            # JobConfig YAMLs + Track A category weights
├── environments/       # shared task-environment helpers (real-world-sim CLIs)
├── harnesses/          # baked openclaw + hermes configs (rich harness image)
├── hooks/              # Harbor TrialEvent hooks (memory-wipe, …)
├── lib/                # adapter subclasses (thin + install-capable)
├── metrics/            # post-run analyzers (Track A weighted aggregator)
├── rubrics/            # Rubric TOMLs for harbor analyze
├── tools/              # sweep drivers + the three status dashboards (below)
└── tasks/              # Harbor task directories
    └── <category>/
        └── <shape>-<NN>/
            ├── task.toml
            ├── instruction.md
            ├── environment/Dockerfile
            └── tests/test.sh
```

## Dashboards

Three self-contained static HTML pages (dark theme, shared top nav, no server —
open from disk). Each has a generator under `tools/`; re-run to refresh.

| Page | Generator | What it shows |
|------|-----------|---------------|
| **Roadmap** (`roadmap.html`) | `tools/roadmap.py` | The PLAN: thesis, where-we-stand, the **epics**, every backlog spec rolled up under one (status + expandable detail + open-full-spec modal). |
| **Task Suite** (`task-catalog.html`) | `tools/task_catalog.py` | The TASKS: an accordion over every task — instruction / grader / oracle / env, plus a per-task **work status** and an **operator-approval** axis (every task is `NEEDS REVIEW` until its `task.toml` sets `approved = true`). |
| **Agent status** (`agent-status.html`) | `tools/agent_status.py` | The HARNESSES: live config / skills / MCP / memory health for openclaw + hermes. |

The work is organized into **epics** (E1 runtime & adapters · E2 fair-comparison
controls · E3 capability infra · **E4 Task Suite** · E5 observability). Epics are
defined in `tools/roadmap.py`; each backlog spec also carries an `Epic:` frontmatter
line (the `backlog/` dir stays flat — see `backlog/README.md`).

## Categories (18)

Code editing, ops/debugging, research/RAG, conversation/persona,
prototyping, designs, insights research, marketing, data analytics,
documentation, code review, test authoring, tool orchestration,
skill authoring, migration, compliance/security, backup/DR,
**real-world-workflows** (2026-05-30: goal-oriented multi-step tasks +
prompt-injection resistance, per
[`backlog/2026-05-30-goal-oriented-real-world-tasks.md`](backlog/2026-05-30-goal-oriented-real-world-tasks.md)).

See [`SHAPES.md`](SHAPES.md) for the first-sweep shape per category and
the multi-axis reward schema.

## Running

```bash
# Clone alongside a Harbor checkout
git clone https://github.com/johnbuck/harbor-tasks.git
cd harbor-tasks

# Single task:
harbor run --path tasks/code-editing/fix-bug-with-failing-test-01 \
    --agent openclaw --agent hermes --model anthropic/claude-sonnet-4-5

# Full sweep (once configs/first-sweep.yaml is authored):
harbor run -c configs/first-sweep.yaml

# View results:
harbor view ./jobs
```

## Related

- [harbor-framework/harbor](https://github.com/harbor-framework/harbor) — upstream framework
- [johnbuck/harbor](https://github.com/johnbuck/harbor) — fork (for any framework-side patches)
