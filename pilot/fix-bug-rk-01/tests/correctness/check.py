# Folder "correctness" -> reward key "correctness". Binary: pytest passes.
import rewardkit as rk

# Use the absolute container interpreter: rewardkit runs under uvx, whose venv
# `python` would otherwise shadow the pytest-equipped image interpreter.
rk.command_succeeds(
    "/usr/local/bin/python -m pytest tests/test_wordcount.py", cwd=".", weight=1.0
)
