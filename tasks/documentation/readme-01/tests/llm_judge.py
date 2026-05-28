"""LLM-judge verifier for readme-01.

Reads the agent's output, asks an Anthropic model to score it against a fixed
rubric, and writes multi-axis scores to /logs/verifier/reward.json.

Robust to SDK churn: uses the plain messages API and parses a JSON object out
of the reply rather than relying on structured-output features.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TARGET = Path("/app/README.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a README file written to document a specific CLI program called greet.py.

The program (greet.py) works as follows:
- It takes a required positional argument: `name` (the person to greet).
- It accepts an optional flag: `--times N` (how many times to print the greeting; default is 1).
- It prints "Hello, <name>!" exactly N times.
- Example: `python greet.py Alice --times 3` prints "Hello, Alice!" three times.

The README must cover ALL FOUR of these elements:
1. What the program does (its purpose/description).
2. How to run it (the command syntax).
3. The command-line arguments: the `name` positional argument AND the `--times` option with its default of 1.
4. At least one example invocation with its expected output shown.

Score these axes, each a float from 0.0 to 1.0:
- correctness: accurately describes greet.py's actual behavior and arguments (name positional arg, --times with default 1, "Hello, <name>!" output format); penalize fabricated flags or wrong defaults.
- instruction_following: covers all four requested elements (purpose, how-to-run, arguments, example with output).
- solution_quality: clear structure, readable, example is runnable and output is correct.
- goal_adherence: documents THIS program (greet.py), no invented features or unrelated content.

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
