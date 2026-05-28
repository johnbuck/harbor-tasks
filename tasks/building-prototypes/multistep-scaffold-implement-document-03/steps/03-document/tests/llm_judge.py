"""LLM-judge verifier for multistep-scaffold-implement-document-03 step 03.

Reads /app/README.md, asks an Anthropic model to score it against a rubric,
and writes a numeric-only reward.json to /logs/verifier/reward.json.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TARGET = Path("/app/README.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a README.md for a small Python package called `tempconv`.

The package contains a single function: c_to_f(c) which converts Celsius to
Fahrenheit using the formula F = C * 9/5 + 32.
Key values: c_to_f(0) == 32.0, c_to_f(100) == 212.0.

Score these axes, each a float from 0.0 to 1.0:
- correctness: does the README accurately describe what c_to_f(c) does (the formula or equivalent description)?
- instruction_following: does it include a description, API reference with parameter and return value, and a runnable usage example?
- solution_quality: is it clearly written and easy to follow?
- goal_adherence: does it stay focused on documenting the tempconv package and c_to_f function?

Respond with ONLY a JSON object, no prose:
{"correctness": <f>, "instruction_following": <f>, "solution_quality": <f>, "goal_adherence": <f>}
"""

AXES = ["correctness", "instruction_following", "solution_quality", "goal_adherence"]


def _zero(reason: str) -> None:
    REWARD.write_text(json.dumps(
        {a: 0.0 for a in AXES} | {"reward": 0.0}, indent=2))
    print(f"reward 0.0 — {reason}")


def main() -> None:
    if not TARGET.exists():
        _zero("no /app/README.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/README.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nREADME:\n{content}"}],
    )
    text = resp.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        _zero(f"judge returned no JSON: {text[:200]}")
        return
    scores = json.JSONDecoder().raw_decode(match.group(0))[0]

    def clamp(x):
        try:
            return max(0.0, min(1.0, float(x)))
        except (TypeError, ValueError):
            return 0.0

    out = {a: clamp(scores.get(a)) for a in AXES}
    out["reward"] = out["correctness"]
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
