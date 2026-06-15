"""Offline unit checks for ExternalContainerEnvironment (lib.external_container).

Encodes spec 2026-06-12-production-agent-eval-mode success criteria:
  #1  stop() NEVER emits a destructive docker subcommand, across all policies.
  #2  start() loud-errors on not-found / not-running; on success resolves and
      addresses ONLY the exact container id thereafter.
  #3  memory_policy gating: wipe refuses without allow_wipe + disposable_pattern
      match (and runs nothing); when allowed emits exactly the configured wipe;
      preserve emits no pre/post memory command at all.
  #5  memory_policy='snapshot' raises NotImplementedError naming the
      restore-verify contract (Phase-2 stub) and destroys nothing.

The docker boundary is mocked via FakeDocker (asyncio.create_subprocess_exec);
all assertions read the recorded docker argv list. No docker daemon is touched.
"""
import pytest

from prod_agent_support import (
    RESOLVED_ID,
    assert_no_destructive,
    make_external_container_env,
    run_async,
)


# --------------------------------------------------------------------------- #
# #1 — stop() never destroys the target, across all three memory policies.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("delete", [True, False])
@pytest.mark.parametrize("policy", ["preserve", "wipe", "snapshot"])
def test_stop_never_emits_destructive_docker_command(
    monkeypatch, tmp_path, policy, delete
):
    overrides = {"memory_policy": policy}
    if policy == "wipe":
        # wipe needs to be explicitly authorized + disposable so start() proceeds.
        overrides.update(
            container="agent-evalcopy",
            allow_wipe=True,
            disposable_pattern="evalcopy",
            wipe_cmd="rm -rf /agent/memory/*",
        )
    env, fake = make_external_container_env(monkeypatch, tmp_path, **overrides)

    async def lifecycle():
        await env.start(force_build=False)
        await env.stop(delete=delete)

    try:
        run_async(lifecycle())
    except NotImplementedError:
        # snapshot is a Phase-2 stub; it must still not have destroyed anything.
        pass

    assert_no_destructive(fake)


# --------------------------------------------------------------------------- #
# #2 — start() resolution + loud failure modes.
# --------------------------------------------------------------------------- #
def test_start_raises_when_container_absent(monkeypatch, tmp_path):
    env, fake = make_external_container_env(monkeypatch, tmp_path)
    fake.set_inspect_not_found()
    with pytest.raises(RuntimeError):
        run_async(env.start(force_build=False))
    assert_no_destructive(fake)


def test_start_raises_when_container_not_running(monkeypatch, tmp_path):
    env, fake = make_external_container_env(monkeypatch, tmp_path)
    fake.set_inspect_not_running()
    with pytest.raises(RuntimeError) as ei:
        run_async(env.start(force_build=False))
    assert "running" in str(ei.value).lower()
    assert_no_destructive(fake)


def test_start_resolves_and_then_addresses_only_the_resolved_id(
    monkeypatch, tmp_path
):
    # Container given by NAME; inspect resolves it to RESOLVED_ID.
    env, fake = make_external_container_env(
        monkeypatch, tmp_path, container="my-prod-agent"
    )
    run_async(env.start(force_build=False))

    before = len(fake.calls)
    run_async(env.exec("echo hi"))
    post_start_tokens = [tok for argv in fake.calls[before:] for tok in argv]

    assert post_start_tokens, "exec emitted no docker command"
    assert RESOLVED_ID in post_start_tokens, (
        "exec must address the resolved container id, not the name"
    )
    assert "my-prod-agent" not in post_start_tokens, (
        "after start() the env must never address the container by name"
    )


# --------------------------------------------------------------------------- #
# #3 — memory_policy gating.
# --------------------------------------------------------------------------- #
def _lifecycle(env):
    async def run():
        await env.start(force_build=False)
        await env.stop(delete=False)

    return run()


def test_wipe_refused_without_allow_wipe_runs_nothing(monkeypatch, tmp_path):
    env, fake = make_external_container_env(
        monkeypatch,
        tmp_path,
        container="agent-evalcopy",
        memory_policy="wipe",
        allow_wipe=False,  # not authorized
        disposable_pattern="evalcopy",  # matches, but allow_wipe gates it
        wipe_cmd="rm -rf /agent/memory/*",
    )
    with pytest.raises(RuntimeError):
        run_async(_lifecycle(env))
    assert not any("/agent/memory" in c for c in fake.commands), (
        "a refused wipe must run no memory command"
    )
    assert_no_destructive(fake)


def test_wipe_refused_when_pattern_does_not_match_runs_nothing(monkeypatch, tmp_path):
    env, fake = make_external_container_env(
        monkeypatch,
        tmp_path,
        container="my-prod-agent",  # does NOT contain 'evalcopy'
        memory_policy="wipe",
        allow_wipe=True,
        disposable_pattern="evalcopy",
        wipe_cmd="rm -rf /agent/memory/*",
    )
    with pytest.raises(RuntimeError):
        run_async(_lifecycle(env))
    assert not any("/agent/memory" in c for c in fake.commands), (
        "wipe on a non-disposable target must run no memory command"
    )
    assert_no_destructive(fake)


def test_wipe_allowed_emits_exactly_the_configured_wipe(monkeypatch, tmp_path):
    env, fake = make_external_container_env(
        monkeypatch,
        tmp_path,
        container="agent-evalcopy",
        memory_policy="wipe",
        allow_wipe=True,
        disposable_pattern="evalcopy",
        wipe_cmd="rm -rf /agent/memory/*",
    )
    run_async(_lifecycle(env))
    assert any("rm -rf /agent/memory/*" in c for c in fake.commands), (
        "an authorized wipe must emit the configured wipe_cmd"
    )
    # The wipe must run against the resolved id, not the name.
    wipe_cmds = [c for c in fake.commands if "rm -rf /agent/memory/*" in c]
    assert all(RESOLVED_ID in c for c in wipe_cmds)
    assert all("agent-evalcopy" not in c for c in wipe_cmds)


def test_preserve_emits_no_memory_command(monkeypatch, tmp_path):
    env, fake = make_external_container_env(
        monkeypatch,
        tmp_path,
        container="my-prod-agent",
        memory_policy="preserve",
        memory_paths=["/agent/memory"],
        wipe_cmd="rm -rf /agent/memory/*",  # set but must be ignored under preserve
    )
    run_async(_lifecycle(env))
    assert not any("/agent/memory" in c for c in fake.commands), (
        "preserve must emit no pre/post memory command"
    )
    assert_no_destructive(fake)


# --------------------------------------------------------------------------- #
# #5 — snapshot is a Phase-2 stub that names the restore-verify contract.
# --------------------------------------------------------------------------- #
def test_snapshot_raises_not_implemented_naming_restore_verify(monkeypatch, tmp_path):
    env, fake = make_external_container_env(
        monkeypatch, tmp_path, memory_policy="snapshot"
    )
    with pytest.raises(NotImplementedError) as ei:
        run_async(_lifecycle(env))
    msg = str(ei.value).lower()
    assert "restore" in msg, "snapshot stub must name the restore step"
    assert "verif" in msg, "snapshot stub must name the verify step"
    assert_no_destructive(fake)
