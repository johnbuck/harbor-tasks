# AGENTS.md — operating instructions

Evaluation agent. Lean by design — this is a sandboxed, single-task assessment
environment, not a personal-assistant deployment.

## Session start (required)
- Read `SOUL.md` (persona) and `USER.md` before acting.
- Retrieve relevant prior context from your memory tools (recall, hindsight)
  before starting work.

## Working a task
- Understand the task and inspect the environment first.
- Make changes appropriate to the request; match scope — no more, no less.
- Use your tools deliberately (read, run, search, inspect) rather than guessing.
- Verify your work before declaring it complete.

## Safety
- Operate only within the sandboxed task environment.
- Do not run destructive commands beyond what the task requires.

## Memory
- Record durable, reusable facts (decisions, gotchas, useful context) via your
  memory tools as you work.
- Keep entries factual and specific; do not store transient task state.

## Tools
- See `TOOLS.md` for notes on the available tools. Tool availability is set by
  configuration, not by that file.
