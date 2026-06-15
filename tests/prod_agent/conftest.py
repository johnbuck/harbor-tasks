"""Make the repo root and this dir importable for the prod-agent offline suite.

These are OFFLINE unit checks for the 2026-06-12-production-agent-eval-mode spec.
They mock docker AT THE BOUNDARY (``asyncio.create_subprocess_exec``) and the
agent environment, so no docker daemon, build, or sweep is needed. Run on the
harbor venv (rewardkit importable).

The parent ``tests/conftest.py`` already puts ``tests/`` on the path (for
``import helpers``); here we add the repo root (so ``import lib.external_*``
resolves once the builder creates those modules) and this directory (so
``import prod_agent_support`` resolves).
"""
import os
import sys

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

for _p in (_REPO_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
