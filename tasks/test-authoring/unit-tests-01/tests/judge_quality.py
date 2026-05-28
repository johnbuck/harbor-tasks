"""Quality half of the mixed unit-tests-01 verifier.

Objective axes (correctness, instruction_following) are passed in via env by
test.sh. This script judges coverage quality of the agent's test file and
writes the final /logs/verifier/reward.json. reward = correctness.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TEST_FILE = Path("/app/tests/test_slugify.py")
REWARD = Path("/logs/verifier/reward.json")

correctness = float(os.environ.get("CORRECTNESS", "0"))
instr = float(os.environ.get("INSTR_FOLLOWING", "0"))


def write(quality: float, goal: float, note: str | None = None) -> None:
    out = {
        "correctness": correctness,
        "instruction_following": instr,
        "solution_quality": quality,
        "goal_adherence": goal,
        "reward": correctness,
    }
    if note:
        REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


def main() -> None:
    if not TEST_FILE.exists():
        write(0.0, 0.0, "no test file")
        return
    src = TEST_FILE.read_text()
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    rubric = (
        "You are grading the quality of a pytest test file written for a "
        "slugify(s) function (lowercases, collapses runs of non-alphanumerics "
        "to a single hyphen, strips leading/trailing hyphens). Score 0.0-1.0:\n"
        "- solution_quality: breadth of coverage (lowercasing, punctuation, "
        "whitespace runs, leading/trailing hyphen stripping, edge cases) and "
        "clear assertions.\n"
        "- goal_adherence: tests genuinely target slugify behavior, not trivial "
        "no-op assertions.\n"
        'Respond with ONLY JSON: {"solution_quality": <f>, "goal_adherence": <f>}'
    )
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=300,
        messages=[{"role": "user", "content": f"{rubric}\n\nTEST FILE:\n{src}"}],
    )
    m = re.search(r"\{.*\}", resp.content[0].text, re.DOTALL)
    if not m:
        write(0.0, 0.0, "judge returned no JSON")
        return
    d = json.JSONDecoder().raw_decode(m.group(0))[0]

    def clamp(x):
        try:
            return max(0.0, min(1.0, float(x)))
        except (TypeError, ValueError):
            return 0.0

    write(clamp(d.get("solution_quality")), clamp(d.get("goal_adherence")))


if __name__ == "__main__":
    main()
