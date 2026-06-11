"""Make ``tests/`` importable so test modules can ``import helpers``.

These are OFFLINE bypass-regression / drift checks for the
2026-06-11-core-eleven-second-adversarial-pass spec. They run on thringle's
harbor venv (rewardkit importable); no docker, no sweep.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
