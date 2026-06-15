# Production-agent eval mode

Attach Harbor to an **already-running** agent container and grade what it says —
instead of building a throwaway `harbor-agents-rich` image and execing a baked
harness inside it. Use this to evaluate a REAL production agent (or a disposable
copy of one), whose accumulated memory is itself the subject of the test.

Spec: `backlog/2026-06-12-production-agent-eval-mode.md`. Three import_path seams
(no Harbor-core fork):

| Seam | Class | Role |
|---|---|---|
| `environment.import_path` | `lib.external_container:ExternalContainerEnvironment` | Attaches to a named/id'd running container; `docker exec` / `docker cp`. **Never builds or destroys it.** |
| `agents[].import_path` | `lib.external_agent:ExternalAgentAdapter` | Drives the agent via its real entrypoint (`invoke`), captures the response. |
| `verifier.import_path` | `lib.external_verifier:ExternalTranscriptVerifier` | Grades the captured transcript **host-side** with a normal rewardkit grader; ignores the prod container. |

## Point it at a real container

1. Copy `configs/prod-agent-example.yaml` and set:
   - `environment.kwargs.container` — the **name or id** of the running container.
   - `agents[0].kwargs.invoke` — the agent's real CLI. `{instruction}` is templated
     in **shell-quoted**, so a hostile-looking message can't break the command.
   - `agents[0].kwargs.response` — how to read the answer: `stdout`, `file:<path>`
     (downloaded via `docker cp`), or `json:<dotted.path>` (a field of stdout JSON).
   - `verifier.kwargs.tests_dir` — the rewardkit grader dir for the task; the captured
     transcript is staged as `answer_filename` (default `answer.md`) before grading.
2. **Preflight first** — attach and report without invoking the agent or touching
   memory:
   ```
   python tools/prod_agent_preflight.py configs/<your-config>.yaml
   ```
   It prints the resolved container id, state, memory policy, and the invoke command
   it WOULD run, then exits — mutating nothing.

## Safety knobs (read before running)

- **`memory_policy: preserve`** (default) — read-only intent; the agent runs against
  its live memory and we only observe. The eval may leave traces (documented tradeoff).
- **`memory_policy: wipe`** — explicit opt-in ONLY. Requires **both**
  `allow_wipe: true` **and** the container name matching `disposable_pattern`
  (e.g. `evalcopy`). When authorized it runs `wipe_cmd` (or clears `memory_paths`);
  otherwise it refuses **loudly and runs nothing**. This mirrors
  `hooks/wipe_memory_state.py`'s `_assert_eval_scope` so a real prod agent can't be
  wiped by fat-finger.
- **`memory_policy: snapshot`** — Phase 2. Will capture state on start and
  restore-and-verify on stop (a failed restore is a hard error). Currently raises
  `NotImplementedError` naming that contract.
- **`stop()` never tears down the target** — no `down`/`rm`/`stop`/`kill`/`--volumes`/
  `--rmi`, regardless of the run's `delete` flag. After the trial the container is
  still running, unmodified.
- After `start()` the environment addresses **only the resolved container id**, never
  the name.

## What's deferred to Phase 2 / manual

`snapshot` memory mode, filesystem-task fixture injection (gated behind `snapshot`),
remote `DOCKER_HOST` targeting, multi-target sweeps, and pointing the mode at an
actual production agent. The code here is built and unit-tested against a throwaway
stand-in (docker mocked at the subprocess boundary); an oracle/`n>=5` run is a manual
post-merge step.
