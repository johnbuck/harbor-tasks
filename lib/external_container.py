"""Attach to an already-running container instead of building a throwaway one.

This is the production-agent eval mode (spec 2026-06-12). Harbor normally owns
the whole container lifecycle: build a task image, run a fresh container, exec a
baked harness inside it, tear it down. A real production agent already runs in
its OWN container, and its accumulated memory IS the thing under test — so we
must NEVER build or destroy it, and must handle its memory under an explicit
policy.

``ExternalContainerEnvironment`` is a ``BaseEnvironment`` referenced by
``environment.import_path`` (no Harbor-core fork). It:

  * ``start()`` — resolves a named/id'd container via ``docker inspect``, asserts
    it exists AND is running (loud ``RuntimeError`` otherwise), captures the
    EXACT container id, and applies the start-side memory policy. It never builds
    and ignores ``force_build``.
  * ``stop()`` — a NO-OP on the container regardless of ``delete``. It never emits
    ``down`` / ``rm`` / ``stop`` / ``kill`` / ``--volumes`` / ``--rmi`` (safety
    §1). Destroying a real prod agent here is the load-bearing failure mode.
  * ``exec`` / ``upload_*`` / ``download_*`` — ``docker exec`` / ``docker cp``
    against the resolved id (never the name — safety §6).

Memory policy (knob, enforced here around the run):

  * ``preserve`` (default) — no-op both ends; observe only.
  * ``wipe`` — explicit opt-in ONLY: requires BOTH ``allow_wipe=True`` AND the
    container name matching ``disposable_pattern`` (mirrors the
    ``_assert_eval_scope`` philosophy in ``hooks/wipe_memory_state.py``); refuses
    loudly and runs nothing otherwise.
  * ``snapshot`` — Phase-2 stub: raises ``NotImplementedError`` naming the
    restore-and-verify contract it must honor before it can ship.
"""

from __future__ import annotations

import asyncio
import json
import re
import shlex
from pathlib import Path

from harbor.environments.base import BaseEnvironment, ExecResult
from harbor.environments.capabilities import EnvironmentCapabilities

_VALID_POLICIES = ("preserve", "wipe", "snapshot")


class ExternalContainerEnvironment(BaseEnvironment):
    """A BaseEnvironment that attaches to an existing container, never building."""

    def __init__(
        self,
        *args,
        container: str,
        memory_policy: str = "preserve",
        docker_host: str | None = None,
        allow_wipe: bool = False,
        disposable_pattern: str | None = None,
        memory_paths: list[str] | None = None,
        wipe_cmd: str | None = None,
        **kwargs,
    ):
        if not container:
            raise ValueError("ExternalContainerEnvironment requires a 'container'.")
        if memory_policy not in _VALID_POLICIES:
            raise ValueError(
                f"Unknown memory_policy {memory_policy!r}; "
                f"expected one of {_VALID_POLICIES}."
            )
        # State the capabilities/validators in super().__init__ may read must be
        # set BEFORE the super call.
        self._container_name = container
        self._memory_policy = memory_policy
        self._docker_host = docker_host
        self._allow_wipe = allow_wipe
        self._disposable_pattern = disposable_pattern
        self._memory_paths = list(memory_paths or [])
        self._wipe_cmd = wipe_cmd
        self._container_id: str | None = None
        super().__init__(*args, **kwargs)

    @staticmethod
    def type() -> str:
        return "external-container"

    @property
    def capabilities(self) -> EnvironmentCapabilities:
        # A foreign container: we cannot enforce GPU/compose/Windows or a
        # NO_NETWORK / ALLOWLIST policy on it, so advertise nothing. The base
        # network validator then rejects NO_NETWORK / ALLOWLIST tasks for us.
        return EnvironmentCapabilities()

    def _validate_definition(self):
        # No Dockerfile / compose file: the environment is the running container.
        return

    # --------------------------------------------------------------------- #
    # docker plumbing
    # --------------------------------------------------------------------- #
    def _docker_base(self) -> list[str]:
        base = ["docker"]
        if self._docker_host:
            base.extend(["-H", self._docker_host])
        return base

    async def _run(
        self, argv: list[str], timeout_sec: int | None = None
    ) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            if timeout_sec:
                out, err = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_sec
                )
            else:
                out, err = await proc.communicate()
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise RuntimeError(
                f"docker command timed out after {timeout_sec}s: {' '.join(argv)}"
            )
        rc = proc.returncode or 0
        return (
            rc,
            out.decode(errors="replace") if out else "",
            err.decode(errors="replace") if err else "",
        )

    def _require_id(self) -> str:
        if self._container_id is None:
            raise RuntimeError(
                "ExternalContainerEnvironment.exec called before start(); "
                "the container has not been resolved yet."
            )
        return self._container_id

    # --------------------------------------------------------------------- #
    # lifecycle
    # --------------------------------------------------------------------- #
    async def start(self, force_build: bool = False) -> None:
        # IGNORE force_build: we never build a foreign container.
        await self._resolve_container()
        await self._apply_memory_policy_start()

    async def _resolve_container(self) -> None:
        rc, out, err = await self._run(
            self._docker_base() + ["inspect", self._container_name]
        )
        if rc != 0 or not out.strip():
            raise RuntimeError(
                f"ExternalContainerEnvironment: target container "
                f"{self._container_name!r} not found (docker inspect rc={rc}). "
                f"{err.strip()}"
            )
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"ExternalContainerEnvironment: could not parse docker inspect "
                f"output for {self._container_name!r}: {exc}"
            ) from exc
        if not data:
            raise RuntimeError(
                f"ExternalContainerEnvironment: target container "
                f"{self._container_name!r} not found (empty docker inspect)."
            )
        info = data[0]
        state = info.get("State") or {}
        if not state.get("Running"):
            raise RuntimeError(
                f"ExternalContainerEnvironment: target container "
                f"{self._container_name!r} is not running "
                f"(status={state.get('Status')!r}). Start it before attaching."
            )
        resolved = info.get("Id")
        if not resolved:
            raise RuntimeError(
                f"ExternalContainerEnvironment: docker inspect for "
                f"{self._container_name!r} returned no container Id."
            )
        # From here on we address ONLY this id, never the name (safety §6).
        self._container_id = resolved

    async def stop(self, delete: bool = False) -> None:
        # NEVER tear down the target — regardless of `delete`. We emit no
        # down/rm/stop/kill/--volumes/--rmi (safety §1). The container and its
        # state outlive the trial untouched.
        await self._apply_memory_policy_stop()

    # --------------------------------------------------------------------- #
    # memory policy
    # --------------------------------------------------------------------- #
    async def _apply_memory_policy_start(self) -> None:
        if self._memory_policy == "preserve":
            return
        if self._memory_policy == "snapshot":
            raise NotImplementedError(
                "memory_policy='snapshot' is a Phase-2 stub. It must CAPTURE the "
                "agent's memory on start and RESTORE it on stop, then VERIFY the "
                "restore succeeded (a failed/partial restore is a hard error, "
                "never a warning). That restore-and-verify contract is not "
                "implemented yet — use 'preserve' or an explicit 'wipe'."
            )
        if self._memory_policy == "wipe":
            # Validate BEFORE running anything: a refused wipe runs nothing.
            self._assert_wipe_allowed()
            await self._run_wipe()

    async def _apply_memory_policy_stop(self) -> None:
        # preserve / wipe have no stop-side action; snapshot (Phase 2) would
        # restore-and-verify here, but it refuses at start until implemented.
        return

    def _assert_wipe_allowed(self) -> None:
        if not self._allow_wipe:
            raise RuntimeError(
                "memory_policy='wipe' refused: allow_wipe is not True. Wiping a "
                "production agent's memory is destructive and must be explicitly "
                "authorized."
            )
        if not self._disposable_pattern:
            raise RuntimeError(
                "memory_policy='wipe' refused: no disposable_pattern is "
                "configured, so the target cannot be proven disposable."
            )
        if not re.search(self._disposable_pattern, self._container_name):
            raise RuntimeError(
                f"memory_policy='wipe' refused: target "
                f"{self._container_name!r} does not match disposable_pattern "
                f"{self._disposable_pattern!r}. Refusing to wipe a "
                "non-disposable container."
            )

    async def _run_wipe(self) -> None:
        if self._wipe_cmd:
            self._assert_wiped(await self.exec(self._wipe_cmd, user="root"), self._wipe_cmd)
            return
        if self._memory_paths:
            cmd = " && ".join(
                f"rm -rf {shlex.quote(p.rstrip('/'))}/*" for p in self._memory_paths
            )
            self._assert_wiped(await self.exec(cmd, user="root"), cmd)
            return
        raise RuntimeError(
            "memory_policy='wipe' authorized but neither wipe_cmd nor "
            "memory_paths is configured; nothing to wipe."
        )

    @staticmethod
    def _assert_wiped(result, cmd: str) -> None:
        # A wipe that exits nonzero (bad path, permission, non-root) must NOT look
        # like success: returning normally would leave stale memory across trials
        # while the caller believes it was cleared.
        if getattr(result, "return_code", 0) != 0:
            raise RuntimeError(
                f"memory_policy='wipe' FAILED: command exited "
                f"{result.return_code}: {cmd!r}. Memory was NOT cleared; refusing "
                "to proceed as if it had been."
            )

    # --------------------------------------------------------------------- #
    # exec / cp
    # --------------------------------------------------------------------- #
    async def exec(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_sec: int | None = None,
        user: str | int | None = None,
    ) -> ExecResult:
        container_id = self._require_id()
        user = self._resolve_user(user)
        env = self._merge_env(env)

        argv = self._docker_base() + ["exec"]
        effective_cwd = cwd or self.task_env_config.workdir
        if effective_cwd:
            argv.extend(["-w", effective_cwd])
        if env:
            for key, value in env.items():
                argv.extend(["-e", f"{key}={value}"])
        if user is not None:
            argv.extend(["-u", str(user)])
        argv.append(container_id)
        argv.extend(["sh", "-c", command])

        rc, out, err = await self._run(argv, timeout_sec=timeout_sec)
        return ExecResult(stdout=out, stderr=err, return_code=rc)

    async def upload_file(self, source_path: Path | str, target_path: str) -> None:
        container_id = self._require_id()
        rc, out, err = await self._run(
            self._docker_base()
            + ["cp", str(source_path), f"{container_id}:{target_path}"]
        )
        if rc != 0:
            raise RuntimeError(f"docker cp upload failed (rc={rc}): {err or out}")

    async def upload_dir(self, source_dir: Path | str, target_dir: str) -> None:
        await self.upload_file(source_dir, target_dir)

    async def download_file(
        self, source_path: str, target_path: Path | str
    ) -> None:
        container_id = self._require_id()
        rc, out, err = await self._run(
            self._docker_base()
            + ["cp", f"{container_id}:{source_path}", str(target_path)]
        )
        if rc != 0:
            raise RuntimeError(f"docker cp download failed (rc={rc}): {err or out}")

    async def download_dir(
        self, source_dir: str, target_dir: Path | str
    ) -> None:
        await self.download_file(source_dir, target_dir)
