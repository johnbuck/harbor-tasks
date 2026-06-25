Author **16 distinct Claude Code subagent definition files**, one per specialist role, under `/app/agents/`.

Each file must be named `/app/agents/<name>.md` and must be a Markdown file beginning with YAML frontmatter (delimited by `---`) containing at minimum these two fields:

- `name:` — the subagent's identifier, matching the filename stem exactly.
- `description:` — a one- or two-sentence description that makes clear *when* this subagent should be invoked. It must mention the **trigger** keyword shown in the table below so an orchestrator can route to it.

After the closing `---` of the frontmatter, write a focused system prompt that defines the subagent's role. The body must:

- Be at least 40 words long.
- Mention the **focus keyword** for that role (case-insensitive).
- Mention the role's own **`name:`** verbatim somewhere in the body (so each agent's prompt is genuinely about itself, not a copy-paste stub for a different role).
- Scope the agent to its single specialty — it must explicitly state it is NOT a general-purpose assistant (include a phrase such as "not a general-purpose assistant", "only", "solely", "sole purpose", "nothing else", "single specialty", or "redirect").

Produce all 16 of these subagents:

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
| `incident-responder.md`| `incident-responder`| `incident`      | `postmortem`   |
| `accessibility-auditor.md`| `accessibility-auditor`| `accessibility` | `wcag`     |
| `i18n-localizer.md`    | `i18n-localizer`    | `localization`  | `translation`  |
| `release-manager.md`   | `release-manager`   | `release`       | `changelog`    |
| `observability-engineer.md`| `observability-engineer`| `observability` | `telemetry`|
| `threat-modeler.md`    | `threat-modeler`    | `threat`        | `attack`       |

Notes:

- The **trigger** keyword must appear in the `description:` field, and the **focus** keyword must appear in the **body** (after the frontmatter).
- Three roles are easy to confuse. **`security-auditor`** (trigger `security`, focus `vulnerability`) and **`threat-modeler`** (trigger `threat`, focus `attack`) are different agents — do not collapse them. **`doc-writer`** (trigger `document`, focus `documentation`) and **`api-designer`** (trigger `api`, focus `endpoint`) both touch APIs — keep them distinct.
- `i18n-localizer`'s trigger is the full word **`localization`** (not `i18n`), and `observability-engineer`'s trigger is **`observability`** (not `monitoring`). A near-synonym is not sufficient.
- Each body must contain its own `name:` verbatim.

Write only the 16 files under `/app/agents/`. No other files or commentary.
