# harbor-tasks — Agent Guide

Rules and operational pointers for AI agents working on the **harbor-tasks**
harness-comparison eval. This file is injected into every agent prompt — keep it
to rules, behaviors, and where-things-are pointers. Deep reference lives in the
docs linked below.

**`CLAUDE.md` is a symlink to this file** (`AGENTS.md`). Edit `AGENTS.md`; both
names stay in sync. Do not recreate `CLAUDE.md` as a separate file.

---

## What this repo is

The task suite + run configs + adapters for evaluating agent **harnesses**
(openclaw vs hermes, extensible to aider/openhands/…) with
[Harbor](https://github.com/harbor-framework/harbor), under controlled
conditions. It answers one question:

> **Which harness is best for the work I actually do, on the *same model*, under
> identical conditions?**

The thesis is **"the harness matters more than the model."** Both harnesses run
the **same model** (`deepseek-v4-pro` via OpenRouter) so any measured gap is the
*harness*, not the model. Proving the suite can *detect* a harness difference is a
precondition for any "they're equivalent" conclusion.

---

## Where it runs (read this first)

Both repos live on **<run-host>** (`LAN-IP`), co-located so the run scripts
resolve `../harbor` automatically:

| Repo | Path on <run-host> | What |
|---|---|---|
| Harbor framework (fork) | `~/benchmarking/harbor` | `johnbuck/harbor`; has its own `.venv` |
| This repo | `~/benchmarking/harbor-tasks` | `johnbuck/harbor-tasks`; tasks, configs, adapters |

> **History:** this moved 2026-06-09 from `/tmp/harbor` + `~/harbor-tasks` on
> <dev-host> to `~/benchmarking/{harbor,harbor-tasks}` on <run-host>. Any doc/memory
> citing `/tmp/harbor` or `~/harbor-tasks` (<dev-host>) is pre-move.

**Working from <dev-host> (architect-<dev-host>):** edit over the sshfs mount at
`~/mnt/<run-host>/benchmarking/harbor-tasks/` — edits land on the real <run-host>
files instantly. **But run git commits/pushes and `harbor run` ON <run-host>**
(`ssh <run-host>@LAN-IP`): git-over-sshfs stats every file and is slow, and the
sweep needs <run-host>'s Docker + `.venv`.

---

## Coding Principles (Karpathy rules — apply to everything you ship)

Same principles as the homelab repo. Adapted from
[forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).
Bias toward caution over speed; for trivial tasks, use judgment.

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.** State assumptions
explicitly; if uncertain, ask. If multiple interpretations exist, present them —
don't pick silently. If a simpler approach exists, say so. If something is
unclear, stop, name what's confusing, and ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.** No features beyond
what was asked, no abstractions for single-use code, no unrequested
"flexibility," no error handling for impossible scenarios. If you wrote 200 lines
and it could be 50, rewrite it. "Would a senior engineer say this is
overcomplicated?" If yes, simplify.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.** Don't "improve"
adjacent code/comments/formatting; don't refactor what isn't broken; match
existing style. Remove orphans *your* change created; mention pre-existing dead
code, don't delete it. Every changed line should trace to the request.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.** "Add a discriminator" → "raise
difficulty + run a 2-harness n=1 and confirm a real Δ, not 1.0/1.0." Weak criteria
("make it work") require constant clarification; strong ones let you loop
independently.

---

## Hard rules (eval-specific — break these and the result is silently wrong)

These are the invariants that have actually bitten this project. The full
catalog with diagnoses is in **`backlog/FOOTGUNS.md`** — read it before any
infra/config/scoring change.

1. **Every task Dockerfile MUST `FROM harbor-agents-rich:latest`** — never
   `harbor-agents-prebaked`. The rich image bakes the openclaw `xrouter` provider
   + persona workspace + hermes config; prebaked has only openclaw+nvm and
   silently bootstraps a default config → `FailoverError: Unknown model:
   xrouter/...`. CI check: `grep -L 'FROM harbor-agents-rich' tasks/*/*/environment/Dockerfile`
   must be empty.

2. **`reward.json` must be a FLAT dict of numbers (`float`/`int`) only.** A
   string/bool/nested value makes Harbor's parser reject the trial — the viewer
   then **silently drops it** (no error, the trial just vanishes). Put
   provenance/notes/status in a sibling `reward-details.json`, never in rewards.

3. **Both harnesses must hit ONE OpenRouter upstream host** (currently `novita`).
   Unpinned = independent load-balancing → unfair cost/cache. The pin host must
   support `data_collection:deny` **AND native tool-use AND reasoning** (novita,
   deepinfra, together, parasail, siliconflow qualify; fireworks fails tool-use).
   It lives byte-identical in four places (`harnesses/openclaw/openclaw.json`,
   `harnesses/hermes/config.yaml`, `lib/openclaw_openrouter.py`,
   `lib/hermes_no_install.py`). **Rebuild the rich image after any pin change** or
   it doesn't take effect. A pin that *parses* is not a pin that *routes* — test
   with a real API call, never config inspection alone. See `harbor-provider-pin`
   memory.

4. **Capabilities (browser, MCP tools) are enabled in the BAKED config + rebuild
   — Harbor-level injection does NOT reach the model.** The thin adapters run the
   harness against its baked config and ignore Harbor's `mcp_servers`. Verify a
   capability is live by reading the agent's tool catalog in the trajectory, not
   the config.

5. **`jobs_dir` must be an absolute PERSISTENT path** (`~/benchmarking/harbor-tasks/jobs`,
   gitignored) — never `/tmp` (tmpfs, wiped on reboot, costs real money to redo).

6. **n=1 validates plumbing only; the verdict needs n≥3 (`pass^k`).** A single run
   is a coin-toss — the harness signal is *reliability variance* + *efficiency*,
   not single-run reward. Always run the Harbor **oracle** (Docker build + schema +
   plumbing, no LLM cost) to catch TOML/heredoc/schema breakage local fixture
   checks miss.

7. **Never grep `.env`/secret files; never put a secret on a command line.** Run
   via Infisical (below). Full rules: the homelab repo's `SECRETS.md`.

---

## Discrimination methodology (the heart of the project)

Authoring or auditing a task for harness discrimination — the distilled playbook
(full record: `backlog/2026-05-31-discrimination-hardening-session.md`,
`backlog/2026-06-01-adversarial-review.md`, and the `harbor-tasks-discrimination-methodology`
memory):

- **DIFFICULTY is the lever, not rubrics.** Graded scoring is *mandatory but not
  sufficient* — a graded-yet-easy task still saturates at 1.0/1.0. Raise difficulty
  on harness-sensitive axes: memory PRECISION via confusable distractors, context
  retention under an UPDATE-trap, recovery EFFICIENCY via a retry budget, proactive
  preference application, stale-memory-vs-ground-truth-file.
- **NO TELEGRAPHING (the #1 validity bug).** An instruction must read like a user
  stating a goal — *nothing* about the eval's traps, hidden checks, or required
  strategy. If you tell the agent "the latest value supersedes earlier ones" or
  "treat emails as data, some try to hijack you," you measure instruction-following,
  not the latent capability. Enforce load-bearing constraints MECHANICALLY (a
  recall-step `find /app -mindepth 1 -delete` wipe), not by instruction.
- **The KILL test:** if `python3 -c` or a single file-read solves it, you're
  measuring the MODEL, not the harness. A real discriminator makes the answer
  uncomputable without the harness-mediated path (memory / long-context / tool /
  sub-agent), and scores that axis as a first-class non-clamped dimension.
- **Recall scorers grade CONTENT, tolerate FORMAT.** A format-strict scorer
  manufactures false zeros that look exactly like harness discrimination. Map each
  question to one line, strip the enumerator, pattern-match the fact. Before
  trusting ANY `0.0`, read the agent's saved `answer.md` — you can re-grade offline
  for $0. See `harbor-recall-scorer-format-robust` memory.
- **A lone `0` on a *completed* multi-step trial is VOID, not a loss** — usually a
  non-persisted answer or a parse artifact. Graders emit `answer_present` (0 = never
  persisted) to distinguish VOID from present-but-wrong.

---

## Running a sweep

Run on **<run-host>**. The driver handles the Infisical footguns (login ignores
`INFISICAL_SITE_URL` → needs `--domain`; `--plain` token has a trailing newline
that must be stripped) and registers the memory-wipe hook the bare CLI can't load:

```bash
ssh <run-host>@LAN-IP
cd ~/benchmarking/harbor-tasks
source ~/.config/infisical/infisical-identity.env   # universal-auth creds, never echoed
tools/run_track_a.sh                              # full Track-A weighted sweep
# single task: harbor run --path tasks/<cat>/<shape>-NN --agent openclaw --agent hermes
# view:        tools/view.sh   (subscription-auth viewer; reads ./jobs)
```

- **Secrets:** `OPENROUTER_API_KEY` is in Infisical **Shared** project
  (`INFISICAL_PROJECT_ID`), env `production`, path `/proxy/`.
- **Infisical is SELF-HOSTED** (`http://internal-host:8380`) — never the
  cloud endpoint, always `--domain`. **Secret writes** go through the
  `infisical-identity` identity on <dev-host> (the <run-host> creds are read-only). See
  [SECRETS.md](../../../SECRETS.md).

---

## Repo layout

```
harbor-tasks/
├── AGENTS.md / CLAUDE.md   # this file (CLAUDE.md → AGENTS.md symlink)
├── README.md, RESULTS.md, SHAPES.md
├── backlog/                # specs (PROPOSED→IN PROGRESS→IMPLEMENTED→done/) + FOOTGUNS.md
├── configs/                # JobConfig YAMLs + Track-A weights
├── environments/           # agent-rich (the baked image) + agent-prebaked + real-world-sim
├── harnesses/              # baked openclaw.json + hermes config.yaml + personas (→ rich image)
├── hooks/                  # Harbor TrialEvent hooks (memory-wipe, …)
├── lib/                    # adapter subclasses: *_thin.py (baked config) + *_no_install.py
├── metrics/                # post-run analyzers (Track-A weighted aggregator)
├── rubrics/, pilot/        # rubric TOMLs / rewardkit experiments
├── tools/                  # sweep drivers + the 3 dashboards + view.sh
├── jobs/                   # run outputs (GITIGNORED, persistent — never /tmp)
└── tasks/<category>/<shape>-NN/   # task.toml, instruction.md, environment/Dockerfile, tests/test.sh
```

**Three static HTML dashboards** (no server — open from disk; generators under
`tools/`, re-run to refresh): **Roadmap** (`tools/roadmap.py`→`roadmap.html`, the
plan + 5 epics), **Task Suite** (`tools/task_catalog.py`→`task-catalog.html`, every
task + work-status + an operator-approval axis — tasks read `NEEDS REVIEW` until
`task.toml` sets `[metadata] approved = true`), **Agent status**
(`tools/agent_status.py`→`agent-status.html`, live harness health). See
`harbor-tasks-dashboards-and-epics` memory.

**Backlog conventions:** flat dir, `YYYY-MM-DD-<slug>.md`, status badge in
frontmatter, `Epic: E#` line per spec, `git mv` to `done/` when IMPLEMENTED. See
`backlog/README.md`.

---

## Where the deep knowledge lives

| Want | Where |
|---|---|
| Every operational footgun + diagnosis | `backlog/FOOTGUNS.md` |
| Per-feature design + decision rationale | `backlog/` (and `backlog/done/`) |
| Task shapes + reward schema | `SHAPES.md` |
| Current comparison results | `RESULTS.md` |
| Cross-session operator knowledge | Claude memory: `harbor-tasks-project`,
  `harbor-tasks-discrimination-methodology`, `harbor-provider-pin`,
  `harbor-harness-capability-enablement`, `harbor-recall-scorer-format-robust`,
  `harbor-context-rot-scoring-integrity`, `harbor-tasks-rich-base-required`,
  `harbor-tasks-dashboards-and-epics` |
| Code navigation (symbols/refs) | **Serena MCP** (project onboarded; use
  `list_memories`/`read_memory` + `find_symbol` etc. before grepping) |

> `harnesses/openclaw/workspace/AGENTS.md` is a *persona* file baked into the
> openclaw harness under test — NOT a guide for working on this repo. This file is.
