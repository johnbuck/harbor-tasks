#!/usr/bin/env bash
# Suite sweep driver: loads the YAML, registers the memory-wipe hook, runs
# the job, then runs the weighted-aggregation post-processor.
#
# Spec: backlog/2026-05-30-harness-vs-model-discriminating-suite.md
#
# Infisical-CLI footguns this wrapper handles for you:
#   1. `infisical login` ignores INFISICAL_SITE_URL — needs explicit --domain.
#   2. `infisical run` ditto.
#   3. `--plain --silent` emits the token WITH a trailing newline; stashing
#      that in INFISICAL_TOKEN unstripped breaks the next HTTP call with
#      `invalid header field value for "Authorization"` (\n in header). Strip
#      with `tr -d '\r\n'` before exporting.
#
# Usage:
#   source ~/.config/infisical/infisical-identity.env
#   tools/run_suite.sh

set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
HARBOR="${HARBOR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../harbor" && pwd)}"
CONFIG="${CONFIG:-${REPO}/configs/suite.yaml}"
WEIGHTS="${REPO}/configs/suite-weights.toml"
# Persistent jobs dir on the encrypted /home (327G), NOT /tmp — /tmp is tmpfs
# (RAM-backed) so runs there are wiped on reboot and cost real money to redo.
# harbor-tasks/jobs/ is gitignored, so it persists without bloating the repo.
JOBS_DIR="${JOBS_DIR:-${REPO}/jobs}"
JOB_NAME="${JOB_NAME:-suite-$(date +%Y-%m-%d__%H-%M-%S)}"

# Internal endpoints + Infisical coords come from the gitignored configs/local.env
# (template: configs/local.env.example). Keeps topology out of this public repo.
[ -f "$REPO/configs/local.env" ] && { set -a; . "$REPO/configs/local.env"; set +a; }
SITE_URL="${INFISICAL_SITE_URL:?set INFISICAL_SITE_URL in configs/local.env (see configs/local.env.example)}"
PROJECT_ID="${INFISICAL_PROJECT_ID:?set INFISICAL_PROJECT_ID in configs/local.env (see configs/local.env.example)}"

: "${INFISICAL_CLIENT_ID:?set INFISICAL_CLIENT_ID via ~/.config/infisical/infisical-identity.env}"
: "${INFISICAL_CLIENT_SECRET:?set INFISICAL_CLIENT_SECRET via ~/.config/infisical/infisical-identity.env}"

# Acquire token via universal-auth → tempfile (never echo). Strip trailing
# newline before stashing in INFISICAL_TOKEN (HTTP-header safety).
TOK_TMP="$(mktemp -t itok.XXXXXX)"
chmod 600 "$TOK_TMP"
trap 'rm -f "$TOK_TMP"' EXIT
infisical login \
    --method=universal-auth \
    --client-id="$INFISICAL_CLIENT_ID" \
    --client-secret="$INFISICAL_CLIENT_SECRET" \
    --domain="$SITE_URL" \
    --plain --silent >"$TOK_TMP" 2>/dev/null
export INFISICAL_TOKEN="$(tr -d '\r\n' < "$TOK_TMP")"
export INFISICAL_SITE_URL="$SITE_URL"
export PATH="${HARBOR}/.venv/bin:${PATH}"

# Optional ANTHROPIC_API_KEY, scoped to its own Infisical project (Harbor) and
# used ONLY by Harbor — for the alternate-model (Anthropic) agent axis and the
# LLM-judge verifiers. Fetched with the token we already acquired and EXPORTED so
# the run inherits it (the value never lands on a command line). No-op when
# INFISICAL_ANTHROPIC_PROJECT_ID is unset, so deepseek/OpenRouter runs are
# unaffected. The OpenRouter key still comes from the Shared project below.
if [ -n "${INFISICAL_ANTHROPIC_PROJECT_ID:-}" ]; then
    # Secret is named BH_ANTHROPIC_API_KEY in Infisical but EXPORTED as the
    # standard ANTHROPIC_API_KEY that the Anthropic SDK / both harnesses read.
    ANTHROPIC_API_KEY="$(infisical secrets get "${INFISICAL_ANTHROPIC_SECRET_NAME:-BH_ANTHROPIC_API_KEY}" \
        --projectId="$INFISICAL_ANTHROPIC_PROJECT_ID" \
        --env="${INFISICAL_ANTHROPIC_ENV:-prod}" \
        --path="${INFISICAL_ANTHROPIC_PATH:-/proxy}" \
        --token="$INFISICAL_TOKEN" --domain="$SITE_URL" \
        --plain --silent 2>/dev/null | tr -d '\r\n')"
    export ANTHROPIC_API_KEY
fi

# Inject secrets and run the sweep programmatically (so we can register the
# memory-wipe TrialEvent.START hook — the `harbor run -c <yaml>` CLI does NOT
# load hooks).
infisical run \
    --domain="$SITE_URL" \
    --projectId="$PROJECT_ID" \
    --env=production --path=/proxy/ \
    -- env JOB_NAME="$JOB_NAME" REPO="$REPO" CONFIG="$CONFIG" \
       N_ATTEMPTS="${N_ATTEMPTS:-}" JOBS_DIR="$JOBS_DIR" \
       PYTHONPATH="${REPO}:${PYTHONPATH:-}" \
       uv run --project "$HARBOR" python - <<'PY'
import asyncio
import os
import sys
from pathlib import Path

import yaml
from harbor.job import Job
from harbor.models.job.config import JobConfig
from harbor.trial.hooks import TrialEvent
from hooks.wipe_memory_state import wipe_memory_state
from hooks.seed_stale_memory import seed_stale_memory


async def main() -> int:
    cfg_path = Path(os.environ["CONFIG"])
    raw = yaml.safe_load(cfg_path.read_text())

    def _expand(v):
        if isinstance(v, str):
            return os.path.expandvars(v)
        if isinstance(v, list):
            return [_expand(x) for x in v]
        if isinstance(v, dict):
            return {k: _expand(x) for k, x in v.items()}
        return v
    raw = _expand(raw)
    raw["job_name"] = os.environ.get("JOB_NAME", "suite")
    # Pin the ABSOLUTE jobs_dir so Harbor writes to the persistent /home dir
    # regardless of CWD (default is CWD-relative "jobs", which caused runs to
    # scatter between /tmp and the repo).
    if os.environ.get("JOBS_DIR"):
        raw["jobs_dir"] = os.environ["JOBS_DIR"]
    # N_ATTEMPTS env overrides the YAML value (smoke=1 vs pass^k=5) without
    # editing the config — avoids leaving a stale n=1 in the committed YAML.
    if os.environ.get("N_ATTEMPTS"):
        raw["n_attempts"] = int(os.environ["N_ATTEMPTS"])

    # EXCLUDE status="deprecated" tasks. Harbor selects local tasks by directory
    # path and does NOT read the task.toml [metadata] status, so a category-path
    # dataset still sweeps in retired tasks. We scan each local dataset dir for
    # task.tomls carrying `status = "deprecated"` and inject their DIRECTORY
    # names (what Harbor's exclude_task_names fnmatches against — LocalTaskId.
    # get_name() returns the dir basename) into that dataset's
    # exclude_task_names. Keeps the config declarative (just category paths)
    # while guaranteeing no run scores a deprecated task. Set
    # INCLUDE_DEPRECATED=1 to opt out (e.g. to re-validate a retired task).
    import re as _re
    if not os.environ.get("INCLUDE_DEPRECATED"):
        _dep_re = _re.compile(r'(?m)^\s*status\s*=\s*["\']deprecated["\']')
        excluded = []
        for ds in raw.get("datasets", []):
            if not isinstance(ds, dict) or not ds.get("path"):
                continue
            ds_path = Path(os.path.expanduser(ds["path"]))
            if not ds_path.is_dir():
                continue
            deprecated_dirs = []
            for child in sorted(ds_path.iterdir()):
                toml = child / "task.toml"
                if toml.is_file() and _dep_re.search(toml.read_text()):
                    deprecated_dirs.append(child.name)
            if deprecated_dirs:
                patterns = list(ds.get("exclude_task_names") or [])
                for name in deprecated_dirs:
                    if name not in patterns:
                        patterns.append(name)
                ds["exclude_task_names"] = patterns
                excluded.extend(deprecated_dirs)
        if excluded:
            print(f"[deprecation-filter] excluding {len(excluded)} deprecated "
                  f"task(s): {', '.join(sorted(excluded))}", file=sys.stderr)

    # ONE JOB PER HARNESS — so each job's dashboard rollup is a single harness's
    # scores and the two jobs compare directly (mixing both agents in one job
    # forces per-task comparison, which defeats the rollup view). One invocation
    # emits `<job_name>__openclaw` and `<job_name>__hermes`.
    base_job_name = os.environ.get("JOB_NAME", "suite")
    agents = raw.pop("agents")

    def _label(a):
        cls = (a.get("import_path") or "").rsplit(":", 1)[-1].lower()
        if "openclaw" in cls:
            return "openclaw"
        if "hermes" in cls:
            return "hermes"
        return cls or "agent"

    for agent_cfg in agents:
        label = _label(agent_cfg)
        sub = dict(raw)
        sub["agents"] = [agent_cfg]
        sub["job_name"] = f"{base_job_name}__{label}"
        config = JobConfig.model_validate(sub)
        job = await Job.create(config)
        job.add_hook(TrialEvent.START, wipe_memory_state)
        # Seed the T3 stale memory AFTER the wipe (order matters: the wipe empties
        # the eval banks, then this writes one stale memory back, scoped to the T3
        # trial only). The bare `harbor run` CLI does not load hooks — same footgun
        # the wipe hook documents — so it is registered here in the driver.
        job.add_hook(TrialEvent.START, seed_stale_memory)
        print(f"[{label}] job={sub['job_name']} {len(job)} trials, "
              f"n_attempts={config.n_attempts}", file=sys.stderr)
        await job.run()
    return 0


sys.exit(asyncio.run(main()))
PY

# Post-run: weighted aggregate + split across the two per-harness job dirs.
OC_DIR="${JOBS_DIR}/${JOB_NAME}__openclaw"
HE_DIR="${JOBS_DIR}/${JOB_NAME}__hermes"
if [[ -d "$OC_DIR" || -d "$HE_DIR" ]]; then
    echo "computing suite weighted report (both harness jobs)..." >&2
    uv run --project "$HARBOR" "${REPO}/metrics/suite_weighted.py" \
        --job-dir "$OC_DIR" --job-dir "$HE_DIR" \
        --tasks-root "${REPO}/tasks" \
        --weights "$WEIGHTS"
else
    echo "WARNING: ${OC_DIR} / ${HE_DIR} not found; skipping weighted report" >&2
fi
