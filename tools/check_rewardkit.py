#!/usr/bin/env python3
"""check_rewardkit.py — enforce THE grading standard: every active task is graded
by rewardkit. No exceptions (pytest included).

A task is COMPLIANT iff its scored grader(s) call rewardkit. Bespoke bash/python
graders and raw `pytest` invocations are NON-compliant. Intermediate steps of a
multi-step task that only write a constant placeholder reward.json (the trial-drop
guard, FOOTGUNS #2) are tolerated — only graders that COMPUTE a reward must use
rewardkit.

Exit non-zero (listing offenders) if any active task is non-compliant. Mirrors the
`FROM harbor-agents-rich` + check_topology CI gates. Archived tasks are not checked.

    python3 tools/check_rewardkit.py
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "tasks"
SKIP = {"_verify"}


def grader_files(task: Path):
    subs = [task / "tests"]
    steps = task / "steps"
    if steps.is_dir():
        subs += sorted(steps.glob("*/tests"))
    out = []
    for sub in subs:
        for name in ("test.sh", "reward.py"):
            p = sub / name
            if p.exists():
                out.append(p)
    return out


def computes_reward(text: str) -> bool:
    """True if the file emits a NON-constant reward (i.e. it grades), vs a pure
    placeholder like `echo '{"reward": 0.0}'`."""
    if "pytest" in text:
        return True
    # any reward emission whose value is not a bare literal
    for m in re.finditer(r'"reward"\s*:\s*([^,}\n]+)', text):
        val = m.group(1).strip().strip('"\'')
        if not re.fullmatch(r'-?\d+(\.\d+)?', val):  # a variable / expression
            return True
    return False


def main() -> int:
    offenders = []
    n_active = 0
    for cat in sorted(TASKS.iterdir()):
        if not cat.is_dir() or cat.name in SKIP:
            continue
        for task in sorted(cat.iterdir()):
            tm = task / "task.toml"
            if not tm.exists() or 'status = "deprecated"' in tm.read_text():
                continue
            n_active += 1
            bad = []
            for g in grader_files(task):
                text = g.read_text(errors="replace")
                if "rewardkit" in text:
                    continue
                if computes_reward(text):
                    kind = "pytest" if "pytest" in text else "bespoke"
                    bad.append(f"{g.relative_to(task)} ({kind})")
            if bad:
                offenders.append((f"{cat.name}/{task.name}", bad))

    compliant = n_active - len(offenders)
    if offenders:
        print(f"check_rewardkit: FAIL — {len(offenders)}/{n_active} active tasks have a "
              f"non-rewardkit grader (standard: 100% rewardkit):", file=sys.stderr)
        for name, bad in offenders:
            print(f"  {name}: {', '.join(bad)}", file=sys.stderr)
        print(f"  ({compliant}/{n_active} compliant)", file=sys.stderr)
        return 1
    print(f"check_rewardkit: OK — all {n_active} active tasks grade via rewardkit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
