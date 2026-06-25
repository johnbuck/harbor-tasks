"""Hygiene + topology gate for the suite tasks (criterion 10).

* No tracked ``__pycache__`` anywhere in the repo.
* Every one of the 21 ``environment/Dockerfile`` is ``FROM harbor-agents-rich:latest``
  (FOOTGUNS #1 — prebaked silently bootstraps a bad config).
* ``tools/check_topology.sh`` exits 0 across the tree.

These are REGRESSION GUARDS: they pass today and the remediation must keep them
green (e.g. not commit a __pycache__, not flip a base image, not leak topology in
a new fixture). Included because criterion 10 requires them verified.
"""
import subprocess

import pytest

from helpers import REPO_ROOT
from suite_helpers import TASKS


def test_no_tracked_pycache():
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files"],
                         capture_output=True, text=True, timeout=60).stdout
    leaked = [ln for ln in out.splitlines() if "__pycache__" in ln or ln.endswith(".pyc")]
    assert not leaked, f"tracked __pycache__/.pyc files: {leaked}"


@pytest.mark.parametrize("tid", list(TASKS), ids=list(TASKS))
def test_dockerfile_from_rich(tid):
    df = REPO_ROOT / TASKS[tid]["dir"] / "environment" / "Dockerfile"
    assert df.exists(), f"{tid}: no environment/Dockerfile"
    assert "FROM harbor-agents-rich:latest" in df.read_text(), \
        f"{tid}: Dockerfile is not FROM harbor-agents-rich:latest"


def test_check_topology_clean():
    proc = subprocess.run(["bash", str(REPO_ROOT / "tools/check_topology.sh")],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"check_topology failed:\n{proc.stdout}\n{proc.stderr}"
