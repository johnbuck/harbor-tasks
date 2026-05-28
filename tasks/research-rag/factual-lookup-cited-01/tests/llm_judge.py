"""LLM-judge verifier for factual-lookup-cited-01.

Reads the agent's answer, asks an Anthropic model to score it against a fixed
rubric, and writes multi-axis scores to /logs/verifier/reward.json.

Robust to SDK churn: uses the plain messages API and parses a JSON object out
of the reply rather than relying on structured-output features.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TARGET = Path("/app/answer.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading an answer to the question: "In what year did the Apollo 11 mission
first land humans on the Moon?"

The correct answer is 1969.

Score these axes, each a float from 0.0 to 1.0:
- correctness: does the answer clearly state 1969 as the year? Score 1.0 only if
  1969 is explicitly present as the stated answer. Score 0.0 if the year is absent
  or a different year is given.
- instruction_following: is a source URL present that starts with http:// or https://?
  Score 1.0 if yes, 0.0 if no URL is present.
- solution_quality: is the answer clear and concise? Does it directly address the
  question without unnecessary padding?
- goal_adherence: does the response stay focused on answering the Apollo 11 question,
  without going off-topic?

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
        _zero("no /app/answer.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/answer.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nANSWER:\n{content}"}],
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
