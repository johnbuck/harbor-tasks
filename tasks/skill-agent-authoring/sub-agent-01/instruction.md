Author **10 distinct Claude Code subagent definition files**, one per specialist role, under `/app/agents/`.

Each file must be named `/app/agents/<name>.md` and must be a Markdown file beginning with YAML frontmatter (delimited by `---`) containing at minimum these two fields:

- `name:` — the subagent's identifier, matching the filename stem exactly.
- `description:` — a one- or two-sentence description that makes clear *when* this subagent should be invoked. It must mention the trigger keyword shown in the table below so an orchestrator can route to it.

After the closing `---` of the frontmatter, write a focused system prompt that defines the subagent's role. The body must:

- Be at least 40 words long.
- Mention the **focus keyword** for that role (case-insensitive).
- Scope the agent to its single specialty — it must explicitly state it is NOT a general-purpose assistant (include a phrase such as "not a general-purpose assistant", "only", or "solely").

Produce all 10 of these subagents:

| filename (`/app/agents/<name>.md`) | `name:` | `description:` must contain trigger | body must mention focus keyword |
|---|---|---|---|
| `code-reviewer.md`     | `code-reviewer`     | `review`        | `bug`          |
| `security-auditor.md`  | `security-auditor`  | `security`      | `vulnerability`|
| `test-writer.md`       | `test-writer`       | `test`          | `coverage`     |
| `doc-writer.md`        | `doc-writer`        | `document`      | `documentation`|
| `refactorer.md`        | `refactorer`        | `refactor`      | `readability`  |
| `perf-profiler.md`     | `perf-profiler`     | `performance`   | `latency`      |
| `dependency-auditor.md`| `dependency-auditor`| `dependency`    | `version`      |
| `migration-planner.md` | `migration-planner` | `migration`     | `rollback`     |
| `api-designer.md`      | `api-designer`      | `api`           | `endpoint`     |
| `db-modeler.md`        | `db-modeler`        | `schema`        | `index`        |

Each subagent is an independent piece of work — there is no shared state between them. Consider whether you can decompose the authoring so that multiple files are produced in parallel.

Write only the 10 files under `/app/agents/`. No other files or commentary.
