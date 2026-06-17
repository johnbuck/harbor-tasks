"""Shared helpers for the offline regrade / exploit / drift checks.

Two ways to drive a real task grader against fixture answers, fully offline:

* ``grade_rewardkit`` — for rewardkit graders (``rewardkit /tests --workspace``).
  We invoke ``rewardkit.run`` in a FRESH subprocess per call, because rewardkit
  caches imported check modules by path (``_import_py_file``), so repeated
  in-process ``run()`` calls would register zero criteria on the 2nd+ fixture.
* ``run_shell_grader`` — for bash graders (``tests/test.sh``) that hardcode
  ``/app`` / ``/var/log`` / ``/logs/verifier``. We rewrite those absolute roots
  to a throwaway temp root and execute the REAL grader text unchanged otherwise.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def grade_rewardkit(tests_dir: Path, workspace: Path) -> dict:
    """Run a rewardkit grader over ``workspace`` and return a flat result dict.

    Keys:
      ``_reward``  -> the flat reward.json value (float)
      ``_score``   -> the reward's aggregate score (float)
      ``<crit>``   -> per-criterion value, keyed by the criterion's registered
                      name (e.g. ``fact:birthday``, ``check:score``, ``needle:1``).
    """
    out = Path(workspace) / "reward.json"
    code = (
        "import sys, rewardkit\n"
        "rewardkit.run(sys.argv[1], workspace=sys.argv[2], output=sys.argv[3])\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code, str(tests_dir), str(workspace), str(out)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"rewardkit run failed for {tests_dir}:\n{proc.stdout}\n{proc.stderr}"
        )
    flat = json.loads(out.read_text())
    details = json.loads((out.with_name("reward-details.json")).read_text())
    reward_block = details.get("reward")
    # Flat layout -> single "reward" group; be tolerant of other shapes.
    if isinstance(reward_block, list):
        reward_block = reward_block[0]
    result: dict = {"_reward": flat.get("reward"), "_score": reward_block.get("score")}
    for c in reward_block.get("criteria", []):
        result[c["name"]] = c["value"]
    return result


def grade_inprocess(reward_py: Path, workspace: Path, patches: dict | None = None) -> dict:
    """Drive a rewardkit ``reward.py`` IN-PROCESS so module-level ABSOLUTE roots
    can be redirected (the analogue of ``run_shell_grader``'s root remap for the
    bash graders).

    Needed for graders that read a hardcoded absolute path the offline host can't
    provide: ``pandas-sql-from-nl-01`` (``/opt/canonical``) and ``tool-selection-01``
    (``/var/log/tool-calls.log``). ``patches`` maps a module global name to the
    value to overwrite it with AFTER import (e.g. ``{"CANONICAL": tmp_canon}``);
    the criterion closures read the module ``__dict__`` so the override takes.

    Returns the same shape as ``grade_rewardkit``: ``_score`` (weighted mean over
    the registered weights) plus each criterion keyed by its registered name.
    """
    import importlib.util

    import rewardkit.session as _S

    sess = _S.Session()
    token = _S._current_session.set(sess)
    try:
        spec = importlib.util.spec_from_file_location("_inproc_grader", reward_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)          # registers criteria into `sess`
        for k, v in (patches or {}).items():
            setattr(mod, k, v)
        result: dict = {}
        acc = 0.0
        total_w = 0.0
        for check, weight in sess.criteria:
            val = check(Path(workspace))
            name = getattr(check, "_criterion_name", getattr(check, "__name__", "?"))
            fval = float(val) if isinstance(val, (bool, int, float)) else val
            result[name] = fval
            if weight:
                acc += float(fval) * weight
                total_w += weight
        result["_score"] = acc / total_w if total_w else 0.0
        return result
    finally:
        _S._current_session.reset(token)


def crit(result: dict, name_substr: str) -> float:
    """Fetch the value of the (single) criterion whose name contains ``name_substr``."""
    matches = [(k, v) for k, v in result.items()
               if not k.startswith("_") and name_substr in k]
    if not matches:
        raise KeyError(f"no criterion matching {name_substr!r} in {sorted(result)}")
    if len(matches) > 1:
        raise KeyError(f"ambiguous {name_substr!r}: {[m[0] for m in matches]}")
    return matches[0][1]


def write_workspace(tmp_path: Path, filename: str, text: str) -> Path:
    ws = tmp_path
    ws.mkdir(parents=True, exist_ok=True)
    (ws / filename).write_text(text)
    return ws


def run_shell_grader(script_path: Path, root: Path, roots=("/logs/verifier", "/var/log", "/app")) -> dict:
    """Execute a bash grader with its absolute roots remapped under ``root``.

    Returns the parsed ``<root>/logs/verifier/reward.json`` (or {} if absent).
    """
    text = Path(script_path).read_text()
    # Longest paths first so nested prefixes are not partially replaced.
    for ap in sorted(roots, key=len, reverse=True):
        text = text.replace(ap, f"{root}{ap}")
    (root / "logs" / "verifier").mkdir(parents=True, exist_ok=True)
    tmp_script = root / "grader.sh"
    tmp_script.write_text(text)
    subprocess.run(["bash", str(tmp_script)], capture_output=True, text=True, timeout=120)
    rj = root / "logs" / "verifier" / "reward.json"
    if not rj.exists():
        return {}
    try:
        return json.loads(rj.read_text())
    except (ValueError, OSError):
        # Present-but-unparseable reward.json == a silently-dropped trial.
        return {}
