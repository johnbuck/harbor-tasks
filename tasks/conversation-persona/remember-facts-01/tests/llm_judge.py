"""LLM-judge verifier for remember-facts-01.

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

TARGET = Path("/app/answer.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a fact-recall answer against a fixed transcript.

The transcript told the agent:
- The user's name is Dana.
- The user has two cats named Pixel and Byte.
- The user is allergic to peanuts.

The agent was asked: "What are my cats' names, and what am I allergic to?"

The answer must:
1. Name BOTH cats correctly: "Pixel" and "Byte" (both must be present).
2. State the allergy correctly: "peanuts".
3. Answer only what was asked (cats' names + allergy).
4. Use the facts from the transcript — not invent different facts.

Score these axes, each a float from 0.0 to 1.0:
- correctness: 1.0 ONLY if Pixel, Byte, AND peanuts are all present and
  correctly stated; 0.5 if only some are present; 0.0 if none are correct.
- instruction_following: whether the answer addresses exactly what was asked
  (cats' names and allergy), without ignoring either question.
- solution_quality: whether the answer is concise and clearly stated.
- goal_adherence: whether the answer uses facts from the transcript rather
  than inventing different names or allergies.

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
