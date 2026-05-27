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
├── SHAPES.md           # the 17 first-sweep task shapes (one per category)
├── configs/            # JobConfig YAMLs for harbor run
├── rubrics/            # Rubric TOMLs for harbor analyze
└── tasks/              # Harbor task directories
    └── <category>/
        └── <shape>-<NN>/
            ├── task.toml
            ├── instruction.md
            ├── environment/Dockerfile
            └── tests/test.sh
```

## Categories (17)

Code editing, ops/debugging, research/RAG, conversation/persona,
prototyping, designs, insights research, marketing, data analytics,
documentation, code review, test authoring, tool orchestration,
skill authoring, migration, compliance/security, backup/DR.

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
