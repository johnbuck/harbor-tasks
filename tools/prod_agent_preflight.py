#!/usr/bin/env python3
"""Dry-run preflight for the production-agent eval mode (spec safety §5, acceptance §5).

Attaches to the target container declared in a JobConfig YAML, resolves it, runs the
configured healthcheck, and REPORTS what a real run WOULD do — the target, the memory
policy, and the invoke command — WITHOUT invoking the agent or mutating any memory.

It deliberately calls only the environment's read-only resolution path (docker
inspect + healthcheck); it never runs the agent and never runs the memory pre-hook,
so a ``memory_policy: wipe`` target is reported, not wiped.

Usage:
    python tools/prod_agent_preflight.py configs/prod-agent-example.yaml
    python tools/prod_agent_preflight.py configs/prod-agent-example.yaml --instruction "ping"

Exits 0 if attachment succeeds, non-zero (with a loud message) otherwise.
"""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from harbor.models.job.config import JobConfig  # noqa: E402
from harbor.utils.import_path import import_class  # noqa: E402
from harbor.environments.base import BaseEnvironment  # noqa: E402
from harbor.models.task.config import EnvironmentConfig as TaskEnvironmentConfig  # noqa: E402
from harbor.models.trial.paths import TrialPaths  # noqa: E402


async def _preflight(config_path: Path, instruction: str) -> int:
    config = JobConfig.model_validate(yaml.safe_load(config_path.read_text()))

    if not config.environment.import_path:
        print("PREFLIGHT FAILED: environment.import_path is not set.", file=sys.stderr)
        return 2
    env_cls = import_class(config.environment.import_path, base=BaseEnvironment)
    env_kwargs = dict(config.environment.kwargs)

    workdir = Path.cwd()
    trial_paths = TrialPaths(trial_dir=workdir / ".preflight-trial")

    env = env_cls(
        environment_dir=workdir,
        environment_name="preflight",
        session_id="preflight",
        trial_paths=trial_paths,
        task_env_config=TaskEnvironmentConfig(),
        **env_kwargs,
    )

    # Read-only attach: resolve the container (docker inspect) — never the memory hook.
    await env._resolve_container()
    await env.run_healthcheck()  # no-op unless a healthcheck is configured

    policy = env_kwargs.get("memory_policy", "preserve")
    invoke = None
    response = None
    if config.agents and config.agents[0].kwargs:
        invoke = config.agents[0].kwargs.get("invoke")
        response = config.agents[0].kwargs.get("response", "stdout")

    print("=== production-agent eval-mode PREFLIGHT (dry run — nothing mutated) ===")
    print(f"  config            : {config_path}")
    print(f"  target (name/id)  : {env_kwargs.get('container')}")
    print(f"  resolved id       : {env._container_id}")
    print("  state             : running")
    print(f"  memory_policy     : {policy}")
    if policy == "wipe":
        wipe_cmd = env_kwargs.get("wipe_cmd")
        paths = env_kwargs.get("memory_paths")
        print(f"  WOULD wipe        : {wipe_cmd or ('clear ' + str(paths))}")
        print(f"  allow_wipe        : {env_kwargs.get('allow_wipe', False)}")
        print(f"  disposable_pattern: {env_kwargs.get('disposable_pattern')!r}")
    elif policy == "snapshot":
        print("  NOTE              : snapshot is Phase-2 (a real run would refuse).")
    if invoke:
        rendered = invoke.replace("{instruction}", shlex.quote(instruction))
        print(f"  response mode     : {response}")
        print(f"  WOULD invoke      : {rendered}")
    print("=== preflight OK: attached, reported, mutated nothing ===")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to the JobConfig YAML.")
    parser.add_argument(
        "--instruction",
        default="<instruction>",
        help="Sample instruction to render into the invoke command (not sent).",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(_preflight(args.config, args.instruction))
    except Exception as exc:  # loud failure: attachment is the whole point
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
