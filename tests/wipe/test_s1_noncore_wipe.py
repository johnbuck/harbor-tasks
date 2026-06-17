"""S1 — scratch-wipe scope extended to the four non-core recall steps (criterion 7).

Each recall step must source ``lib/wipe_scratch.sh`` (copied into its workdir)
BEFORE the /app wipe, with no ``|| true`` swallowing, and its ``tests/test.sh``
must INDEPENDENTLY re-assert the wipe (multi_step.py treats a setup failure only
as a warning) and fail flat 0.0 if scratch survived.

The session-store dimension differs by task TYPE:
  * conv-02 / conv-03 are EXTERNAL-MEMORY recall tasks: the answer must come from
    the memory backend, so the harness SESSION stores are wiped too (like conv-01).
  * context-fill-01 / context-rot-01 are IN-WINDOW retention tasks: the cross-step
    conversation IS the path under test, so the session stores must be PRESERVED
    while off-/app scratch is still wiped.

These are STATIC assertions on the script text (matching tests/wipe/test_s1_wipe.py).
Dynamically executing a script that runs ``find /tmp -delete`` is unsafe on this
shared host, so the wipe is verified by text, not by running it.

RED expectation: today every one of the four wipes only /app (with ``|| true``),
none source wipe_scratch.sh, and no recall test.sh asserts the wipe.
"""
import re

import pytest

from helpers import REPO_ROOT

EXTERNAL_MEMORY = [
    ("conv-02", "conversation-persona/multistep-memory-conversational-02/steps/06-recall"),
    ("conv-03", "conversation-persona/multistep-memory-conversational-03/steps/07-recall"),
]
IN_WINDOW = [
    ("context-fill-01", "context-management/multistep-context-fill-01/steps/19-recall"),
    ("context-rot-01", "context-rot/context-rot-01/steps/19-recall"),
]
ALL = EXTERNAL_MEMORY + IN_WINDOW


def _setup_text(step_rel):
    p = REPO_ROOT / "tasks" / step_rel / "workdir" / "setup.sh"
    return p.read_text() if p.exists() else ""


def _workdir_text(step_rel):
    wd = REPO_ROOT / "tasks" / step_rel / "workdir"
    if not wd.is_dir():
        return ""
    return "\n".join(p.read_text() for p in sorted(wd.glob("*.sh")))


def _testsh_text(step_rel):
    p = REPO_ROOT / "tasks" / step_rel / "tests" / "test.sh"
    return p.read_text() if p.exists() else ""


@pytest.mark.parametrize("label,step_rel", ALL, ids=[s[0] for s in ALL])
def test_setup_sources_wipe_before_app(label, step_rel):
    txt = _setup_text(step_rel)
    assert txt, f"{label}: no workdir/setup.sh"
    assert "wipe_scratch.sh" in txt, f"{label}: setup.sh does not source wipe_scratch.sh"
    assert txt.index("wipe_scratch.sh") < txt.index("/app"), \
        f"{label}: wipe_scratch.sh must be sourced BEFORE the /app wipe"
    assert "|| true" not in txt, f"{label}: wipe still swallows failures with '|| true'"


@pytest.mark.parametrize("label,step_rel", ALL, ids=[s[0] for s in ALL])
def test_workdir_wipes_offapp_scratch(label, step_rel):
    txt = _workdir_text(step_rel)
    for root in ("/tmp", "/var/tmp", "/logs/agent"):
        assert root in txt, f"{label}: wipe does not cover off-/app scratch {root}"
    assert re.search(r"\$HOME|/root", txt), f"{label}: wipe does not cover agent $HOME scratch"
    # External memory backends must NEVER be touched by setup.sh.
    assert not re.search(r"hindsight|honcho|HINDSIGHT_URL|HONCHO", txt, re.I), \
        f"{label}: setup must not touch the external memory backends"


@pytest.mark.parametrize("label,step_rel", ALL, ids=[s[0] for s in ALL])
def test_recall_test_independently_asserts_wipe(label, step_rel):
    txt = _testsh_text(step_rel)
    assert txt, f"{label}: no tests/test.sh"
    assert re.search(r"/tmp|/var/tmp|/logs/agent|\.openclaw|sessions|/app/reports", txt), \
        f"{label}: test.sh does not independently verify the wipe"
    assert re.search(r'"reward"\s*:\s*0(\.0+)?', txt) and re.search(r"exit\s+1", txt), \
        f"{label}: test.sh wipe assertion cannot fail the trial flat 0.0"
    assert "|| true" not in txt, f"{label}: test.sh swallows the wipe assertion with '|| true'"


@pytest.mark.parametrize("label,step_rel", EXTERNAL_MEMORY, ids=[s[0] for s in EXTERNAL_MEMORY])
def test_external_memory_wipes_session_stores(label, step_rel):
    """conv-02/03: the harness session stores are wiped so recall comes from the
    memory backend, not the in-window conversation."""
    txt = _workdir_text(step_rel)
    assert re.search(r"\.openclaw|hermes|HERMES_HOME|sessions", txt), \
        f"{label}: external-memory wipe does not cover the harness session stores"


@pytest.mark.parametrize("label,step_rel", IN_WINDOW, ids=[s[0] for s in IN_WINDOW])
def test_in_window_preserves_session_stores(label, step_rel):
    """context-fill-01 / context-rot-01: in-window retention tasks must PRESERVE
    the harness session stores (the cross-step conversation is the path under
    test) while still wiping off-/app scratch. The setup must invoke the wipe in
    a session-preserving mode (a documented preserve flag), not the default that
    deletes the session JSONL."""
    txt = _workdir_text(step_rel)
    preserve = re.search(
        r"preserve[_-]?session|keep[_-]?session|wipe_sessions\s*=\s*0|"
        r"skip[_-]?session|no[_-]?session|session.*preserv",
        txt, re.I)
    assert preserve, (
        f"{label}: in-window wipe gives no session-preservation signal; the "
        "default wipe_scratch.sh deletes the session stores this task needs")
