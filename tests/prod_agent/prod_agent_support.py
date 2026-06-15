"""Shared fakes + helpers for the prod-agent offline suite.

Mocking discipline (per the baton constraints): we mock at the BOUNDARY, never
the unit under test.

* For ``ExternalContainerEnvironment`` (the env IS the unit): the boundary is the
  OS process spawn. We monkeypatch ``asyncio.create_subprocess_exec`` with
  ``FakeDocker``, which records every docker argv and returns canned output. The
  env's own logic (inspect-parse, id resolution, memory-policy gating, exec/cp
  command construction) runs for real and is asserted on the recorded argv list.
* For ``ExternalAgentAdapter`` (the adapter IS the unit): the boundary is the
  ``BaseEnvironment`` it is handed. We pass ``FakeEnvironment`` which records
  exec calls and serves canned stdout / file payloads. The adapter's render +
  capture + transcript-write logic runs for real.

The ``lib.external_*`` imports are LAZY (inside the factory helpers) so that a
module that does not yet exist fails only the tests that exercise it, with a
clear ImportError naming the missing class — not the whole suite at collection.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

# The exact container id the fake `docker inspect` resolves the NAME to. Tests
# assert the env addresses THIS id (never the name) after start().
RESOLVED_ID = "c0ffee1234deadbeefc0ffee1234deadbeefc0ffee1234deadbeefc0ffee1234"

# docker SUBCOMMANDS / flags that would destroy or mutate the target container.
# A safe env must never emit any of these as a standalone argv token.
FORBIDDEN_DOCKER_TOKENS = {"down", "rm", "stop", "kill", "--volumes", "--rmi"}


def run_async(coro):
    """Drive an async coroutine to completion without pytest-asyncio."""
    return asyncio.run(coro)


class FakeProc:
    """Stand-in for an asyncio subprocess returned by create_subprocess_exec."""

    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self, input=None):  # noqa: A002 - mirror stdlib name
        return self._stdout, self._stderr

    def terminate(self):
        pass

    def kill(self):
        pass


class FakeDocker:
    """Records every docker argv; routes `inspect` to a configurable payload.

    Install with ``monkeypatch.setattr(asyncio, "create_subprocess_exec", fake)``.
    """

    def __init__(self):
        self.calls: list[list[str]] = []
        # Default: a running container resolving to RESOLVED_ID.
        self.inspect_payload: bytes = json.dumps(
            [{"Id": RESOLVED_ID, "State": {"Running": True, "Status": "running"}}]
        ).encode()
        self.inspect_returncode = 0
        self.default_stdout: bytes = b""
        self.default_returncode = 0

    async def __call__(self, *args, **kwargs):
        argv = [str(a) for a in args]
        self.calls.append(argv)
        if "inspect" in argv:
            return FakeProc(self.inspect_payload, b"", self.inspect_returncode)
        return FakeProc(self.default_stdout, b"", self.default_returncode)

    @property
    def commands(self) -> list[str]:
        """Each recorded argv joined into one string (for substring asserts)."""
        return [" ".join(c) for c in self.calls]

    def set_inspect_not_found(self):
        self.inspect_returncode = 1
        self.inspect_payload = b""

    def set_inspect_not_running(self):
        self.inspect_returncode = 0
        self.inspect_payload = json.dumps(
            [{"Id": RESOLVED_ID, "State": {"Running": False, "Status": "exited"}}]
        ).encode()


def make_external_container_env(monkeypatch, tmp_path, **overrides):
    """Construct an ExternalContainerEnvironment with a FakeDocker installed.

    Returns ``(env, fake)``. Lazy-imports lib.external_container so a missing
    module surfaces inside the calling test.
    """
    from harbor.models.task.config import EnvironmentConfig
    from harbor.models.trial.paths import TrialPaths

    import lib.external_container as ec  # lazy: missing module -> this test only

    fake = FakeDocker()
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake)

    kwargs = {"container": "my-prod-agent", "memory_policy": "preserve"}
    kwargs.update(overrides)

    env = ec.ExternalContainerEnvironment(
        environment_dir=tmp_path,
        environment_name="ext",
        session_id="sess",
        trial_paths=TrialPaths(trial_dir=tmp_path),
        task_env_config=EnvironmentConfig(),
        **kwargs,
    )
    return env, fake


def assert_no_destructive(fake: FakeDocker):
    """Assert no recorded docker argv contains a destructive subcommand/flag."""
    for argv in fake.calls:
        bad = FORBIDDEN_DOCKER_TOKENS.intersection(argv)
        assert not bad, f"destructive docker token(s) {bad} emitted in: {argv}"


class FakeEnvironment:
    """Boundary stand-in for the BaseEnvironment handed to the agent adapter."""

    default_user = None

    def __init__(self):
        self.exec_calls: list[dict] = []
        self.exec_stdout: str = ""
        self.exec_returncode: int = 0
        self.download_payload: str = ""
        self.downloaded: list[tuple[str, str]] = []
        self.uploaded: list[tuple[str, str]] = []

    async def exec(self, command, cwd=None, env=None, timeout_sec=None, user=None):
        from harbor.environments.base import ExecResult

        self.exec_calls.append(
            {"command": command, "cwd": cwd, "env": env, "user": user}
        )
        return ExecResult(
            stdout=self.exec_stdout, stderr="", return_code=self.exec_returncode
        )

    async def download_file(self, source_path, target_path):
        self.downloaded.append((str(source_path), str(target_path)))
        Path(target_path).write_text(self.download_payload)

    async def download_dir(self, source_dir, target_dir):
        pass

    async def upload_file(self, source_path, target_path):
        self.uploaded.append((str(source_path), str(target_path)))

    async def upload_dir(self, source_dir, target_dir):
        pass


def make_agent_adapter(tmp_path, invoke, response="stdout", workdir="/home/agent"):
    """Construct an ExternalAgentAdapter (lazy import of lib.external_agent)."""
    import lib.external_agent as ea  # lazy: missing module -> this test only

    return ea.ExternalAgentAdapter(
        logs_dir=tmp_path,
        invoke=invoke,
        response=response,
        workdir=workdir,
    )
