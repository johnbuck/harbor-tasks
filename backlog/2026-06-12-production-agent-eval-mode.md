---
status: APPROVED
epic: E3
date: 2026-06-12
---

# Production-agent eval mode — attach to existing agent containers instead of building throwaway ones

**Epic:** E3 — Eval infra (may warrant its own epic once it grows; tagged E3 for now)
**Date:** 2026-06-12
**Status:** APPROVED 2026-06-12 — three design forks resolved by the operator
same-day (docker-exec reach; configurable memory policy preserve|snapshot|wipe;
both task shapes). MVP can start.
**Origin / triggered-by:** operator wants to evaluate REAL production agents (or
copies of them) that already run in their own containers — not the synthetic
openclaw/hermes harnesses baked into a throwaway `harbor-agents-rich` image.
Because a production agent's accumulated memory IS the thing under test, the
current "wipe memory between trials" model is wrong for it; targeting and memory
handling must become explicit, configurable knobs.

## Problem

Harbor today owns the whole container lifecycle: for each trial it builds a task
image (`FROM harbor-agents-rich`), runs a fresh throwaway container, execs a
**baked** harness CLI inside it (`openclaw agent …` / `hermes chat …`), and tears
the container down at the end. Memory is an external backend wiped per-trial by a
hook keyed on the `eval-<harness>` group. None of that fits a production agent:

- It already runs in **its own container** with its own entrypoint/persona/config
  — not the rich image, not on `/opt/harness/...`, not invoked like openclaw.
- Its **memory is the subject of the test**, so wiping it (or even leaving eval
  traces in it) defeats the purpose.
- It has **no `/app` fixtures** and **no wired `eval-<harness>` backend**.

We need a mode that ATTACHES to a named existing container, invokes the agent the
way that agent is actually invoked, and handles its memory under an explicit
policy — without ever destroying the container or its state.

## Feasibility (grounded in the code, 2026-06-12)

This needs **no Harbor-core fork for the MVP**. Two extension seams already exist:

- `EnvironmentFactory.create_environment_from_config` honors a custom
  `environment.import_path` and forwards `environment.kwargs` to the constructor
  (`harbor/src/harbor/environments/factory.py:295-303`). So a custom
  `BaseEnvironment` subclass referenced by `import_path` is a first-class
  environment with no registry/enum change.
- Agents already load by `import_path` (`agents/factory.py:101-121`); the thin
  adapters prove a custom adapter that execs a command in the handed environment
  is all Harbor needs (`lib/openclaw_thin.py`, `lib/hermes_thin.py` via
  `exec_as_agent`).

The `BaseEnvironment` contract the new env must satisfy
(`harbor/src/harbor/environments/base.py`): `start(force_build)`, `stop(delete)`,
`exec(command, cwd, env, timeout_sec, user)`, `upload_file/dir`,
`download_file/dir`, `run_healthcheck`. The Docker reference implementation builds
via `docker compose up` (`environments/docker/docker.py:537`) and tears down via
`docker compose down [--rmi all --volumes]` (`:582`). Our env replaces both: no
build on start, **no teardown on stop**.

The memory wipe is harbor-tasks, not framework
(`hooks/wipe_memory_state.py`), and already refuses any non-`eval-*` scope via
`_assert_eval_scope` (`:68-79`) — so it is safe-by-default against prod, but we
want an explicit, first-class policy rather than relying on that guard.

## Scope

**In (MVP):**
- A new `ExternalContainerEnvironment(BaseEnvironment)` in `lib/` that attaches to
  a named, already-running container; exec/cp against it; **never builds or
  destroys** it.
- A generic `ExternalAgentAdapter(BaseAgent)` in `lib/` whose invocation command
  is configurable (the agent's real entrypoint), capturing the response.
- A `memory_policy` knob: `preserve` (default), `wipe` (explicit opt-in +
  disposability guard), `snapshot` (capture→restore) — MVP ships `preserve` and
  `wipe`; `snapshot` lands in Phase 2.
- A **target** knob (the container name/id) + a hard safety model (below).
- The **conversational/behavioral task shape**: instruction-in, response-out,
  graded host-side off the captured transcript — no `/app`, no eval backend.
- An example config + a dry-run/preflight that proves attachment without touching
  agent state.

**In (Phase 2):**
- `memory_policy: snapshot` (volume/path snapshot pre, restore post) for
  non-destructive eval of prod copies.
- **Filesystem-task fixture injection**: `docker cp` the task's `/app` fixtures
  into the target, run `setup.sh`/steps via exec, grade via exec — gated behind
  `snapshot` so fixtures don't permanently pollute the agent.
- Remote `DOCKER_HOST` targeting (prod agent on another host); multi-target
  sweeps (one agent entry per container).

**Out:** the HTTP/API reach model (operator chose docker-exec only — revisit if a
future target is API-fronted); any change to the existing synthetic-harness path;
upstreaming the env to Harbor-core as a registered `EnvironmentType` (do it later
if the import_path prototype proves out); evaluating against a live prod agent in
THIS spec's work (the code is built + tested against a throwaway stand-in; pointing
it at real prod is an operator run, not a baton action).

## Design

### Targeting (knob 1)

`environment.import_path: lib.external_container:ExternalContainerEnvironment`
with `environment.kwargs`:
```yaml
environment:
  import_path: lib.external_container:ExternalContainerEnvironment
  kwargs:
    container: my-prod-agent          # name or id of the running container
    memory_policy: preserve           # preserve | snapshot | wipe
    docker_host: null                 # Phase 2: remote daemon (e.g. ssh://host)
```
`start()` resolves the container (`docker inspect`), asserts it exists and is
**running**, and fails loudly otherwise. It does NOT build anything and ignores
`force_build`. `stop()` is a **no-op on the container** regardless of `delete` —
it never runs `down`/`rm`/`--volumes`. `exec` → `docker exec <container> …`;
`upload/download` → `docker cp`.

### Interaction (knob 2a — "how we interact")

`agent.import_path: lib.external_agent:ExternalAgentAdapter` with `agent.kwargs`:
```yaml
agents:
  - import_path: lib.external_agent:ExternalAgentAdapter
    kwargs:
      invoke: "myagent chat --json --message {instruction}"   # {instruction} templated, shell-quoted
      response: stdout            # stdout | file:<path> | json:<jsonpath>
      workdir: /home/agent        # where to exec
```
`run()` generalizes the thin-adapter pattern: set the instruction into the env
(or template it), exec `invoke` in the target container, capture the response per
`response`, write it to `/logs/agent/external.txt`, populate cost/token context if
the agent emits it (best-effort; many won't). This is the single point that knows
how a given production agent is driven.

### Memory policy (knob 2b — "whether/how we clear memory")

A first-class `memory_policy` enforced by the environment around the run:

- **`preserve`** (default): no-op both ends. The agent runs against its live
  memory and we only observe. Safest; eval may leave traces (documented).
- **`snapshot`** (Phase 2): on `start`, capture the agent's state
  (configurable `memory_paths` tar'd to a host file, and/or named-volume tar via a
  helper); on `stop`, clear and restore it, then VERIFY the restore (never leave
  the agent half-restored — a failed restore is a loud error, not a warning).
  This is the non-destructive mode for prod copies.
- **`wipe`**: explicit opt-in only. Requires BOTH `allow_wipe: true` AND a
  disposability assertion — the target must match a configured
  `disposable_pattern` (e.g. name contains `-evalcopy`) — mirroring
  `_assert_eval_scope`'s philosophy so you cannot wipe real prod by fat-finger.
  Wipe runs a configured `wipe_cmd` (or clears `memory_paths`).

### Task shapes

- **Conversational/behavioral (MVP):** a task with no `environment/Dockerfile`
  build step (the environment is the external container). `instruction.md` is the
  prompt; the verifier grades the **captured response transcript host-side**, not
  the prod container's filesystem. New category `tasks/prod-behavioral/` (or a
  shape flag). NOTE: Harbor's verifier normally runs in the task container — for
  this shape the grader must read the captured transcript from the trial's
  `/logs/agent/` rather than the prod container. Confirm whether that needs a
  small Harbor-side verifier-location change or can be done with a host-side
  grader the driver invokes; if Harbor-core is required, that is the one
  framework dependency and gets its own ticket.
- **Filesystem (Phase 2):** inject fixtures via `docker cp`, run steps via exec,
  grade via exec in the target — only under `memory_policy: snapshot`.

### Safety model (load-bearing — a bug here corrupts a real prod agent)

1. `stop()` NEVER tears down the target (no `down`/`rm`/`stop`/`--volumes`).
2. `wipe` requires `allow_wipe: true` + `disposable_pattern` match; refuse
   otherwise with a loud error (the `_assert_eval_scope` pattern).
3. `snapshot` restore is verified; a failed/partial restore is a hard error.
4. Default is `preserve` (read-only intent); a run that would mutate memory
   without an explicit policy is rejected.
5. A `--dry-run`/preflight attaches, runs the healthcheck, and reports what it
   WOULD do (policy, invoke command, target) without invoking the agent or
   touching memory.
6. Never `docker rm -f` by name pattern; only ever address the exact resolved
   container id captured at `start`.

## Acceptance criteria

1. With a throwaway stand-in container (a plain image sleeping, NOT the rich
   image), a config using `ExternalContainerEnvironment` + `ExternalAgentAdapter`
   attaches, execs a configured invoke command, captures the response, and grades
   a conversational task — with **zero build** and the container **still running,
   unmodified** after the trial (`docker inspect` id + state unchanged; no volume
   removed).
2. `memory_policy: preserve` touches no agent state (verified: a sentinel file the
   stand-in writes to its memory path survives the trial untouched).
3. `memory_policy: wipe` refuses unless `allow_wipe: true` AND the container
   matches `disposable_pattern`; when allowed, it clears the configured path and
   says so; when refused, it errors loudly and runs nothing.
4. `stop()` provably never destroys the target across all policies (unit + an
   integration assertion on container id/state/volumes).
5. The preflight/dry-run reports target + policy + invoke command and exits
   without invoking the agent or mutating state.
6. Offline tests cover: container-not-found, container-not-running, wipe-guard
   refusal, restore-failure-is-hard-error (Phase 2 stub), and response capture for
   stdout/file/json response modes.
7. An example config (`configs/prod-agent-example.yaml`) + a short
   `docs`/README note on how to point it at a real container, including the safety
   knobs.

## Open questions

1. **Verifier location for conversational tasks.** Does grading the captured
   transcript host-side need a Harbor-core verifier change, or can the driver run
   a host-side grader? (Determines whether MVP stays fork-free. Investigate first
   thing in the build.)
2. **Snapshot granularity (Phase 2).** In-container path tar vs named-volume tar
   vs the agent's own export/import API — likely per-target configurable; pick a
   sane default (path tar) and make it pluggable.
3. **Cost/token capture.** Production agents won't emit OpenRouter-style usage;
   decide whether behavioral tasks drop the cost dimension or read a per-agent
   usage hook. MVP: best-effort, omit if absent.

## Execution note (baton + manual split)

The env, adapter, memory-policy logic, conversational task shape, safety guards,
and their offline tests go through baton against a **throwaway stand-in
container** (built in the worktree — a plain `sleep` image with a sentinel memory
file), so nothing real is touched. Pointing the mode at an actual production
agent, and the Phase-2 snapshot/fixture-injection work, are deferred operator
steps after the MVP merges and is reviewed.

## Implementation log / as-built (2026-06-15)

MVP built via baton (run wf_dbf51153-cbd) + a post-build review pass. baton's
own review/document/merge stages did NOT run: the pipeline halted at Integrate
when it tried to merge the STALE origin ref (origin had force-diverged from the
local branch because the remediation branch's history was rewritten mid-run).
The build itself completed and committed before that halt, so the code was intact
and verified separately.

### What landed (16 files, ~1.4k lines, all NEW — synthetic path untouched)
- `lib/external_container.py` — `ExternalContainerEnvironment(BaseEnvironment)`:
  attaches to a named running container (resolves to the exact container Id at
  start, addresses only that Id thereafter), exec/`docker cp` via the resolved
  id, `-H <docker_host>` injected on every call. `stop()` NEVER emits
  down/rm/stop/kill/--volumes under any policy or `delete` value. memory_policy
  preserve=no-op / wipe=double-guarded (allow_wipe AND disposable_pattern match,
  fail-closed) / snapshot=raises NotImplementedError (no silent no-op).
- `lib/external_agent.py` — `ExternalAgentAdapter`: renders `{instruction}`
  shell-quoted into a configurable `invoke`, captures response via
  stdout|file:<path>|json:<jsonpath>, writes to the HOST `logs_dir/external.txt`.
- `lib/external_verifier.py` — host-side verifier (open question #1 RESOLVED
  fork-free): grades the captured transcript via rewardkit on the host using the
  custom-verifier import_path in SHARED mode; never touches the prod container.
- `configs/prod-agent-example.yaml`, `tools/prod_agent_preflight.py` (dry-run),
  `tasks/prod-behavioral/conversational-01/`, and `tests/prod_agent/` (25 offline
  checks).

### Open question #1 — RESOLVED, fork-free
A custom `BaseVerifier` via `VerifierFactory.create_verifier_from_import_path`
grades host-side off `logs_dir/external.txt`; SHARED verifier mode is used
(SEPARATE mode would reuse the trial's env import_path and wrongly re-attach to
the prod container). The spec's literal "/logs/agent/external.txt" is the HOST
`agent_dir` file, not an in-container path — there is no /logs bind mount in a
foreign container.

### Post-build review (MINOR) + fixes applied (commit a593409)
All six safety invariants verified HELD (no prod-destroying path). Two MED
eval-integrity bugs fixed: F1 a failed invoke now writes no transcript (VOID, not
a false 0.0 LOSS); F2 a failed wipe now raises instead of looking like success.
Two regression tests added for the previously-uncovered nonzero-return-code paths.
Final: **25/25 offline checks pass.**

### Deferred (unchanged from Scope)
Phase-2 snapshot+restore memory policy and filesystem-task fixture injection;
remote DOCKER_HOST sweeps; pointing the mode at a real production agent (an
operator run — baton only exercised it against fakes/a throwaway stand-in).

### Landing note
Merged locally via fast-forward onto `remediation/core-eleven-2026-06-10`. NOT
pushed: origin/remediation has force-diverged from local (the branch history was
rewritten), so reconciling origin (force-push or reset) is an operator decision
separate from this feature.
