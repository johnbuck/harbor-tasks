Author a Claude Code subagent definition file at `/app/code-reviewer.md`.

The file must be a Markdown file beginning with YAML frontmatter (delimited by `---`) containing at minimum these two fields:

- `name:` — the subagent's identifier (e.g. `code-reviewer`)
- `description:` — a one- or two-sentence description that makes clear when this subagent should be invoked (e.g. when the user wants code reviewed for bugs, security issues, or style)

After the closing `---` of the frontmatter, write a focused system prompt that defines a subagent specialized in reviewing code for:

1. Bugs and logic errors
2. Security vulnerabilities
3. Code style and readability

The system prompt should give the subagent a clear, well-scoped role. It should not try to be a general-purpose assistant — it is a code reviewer and nothing else.

Write only `/app/code-reviewer.md`. No other files or commentary.
