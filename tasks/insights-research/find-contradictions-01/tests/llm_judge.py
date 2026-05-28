"""LLM-judge verifier for find-contradictions-01.

Reads the agent's contradictions report, asks an Anthropic model to score it
against a fixed rubric, and writes multi-axis scores to /logs/verifier/reward.json.

Robust to SDK churn: uses the plain messages API and parses a JSON object out
of the reply rather than relying on structured-output features.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TARGET = Path("/app/contradictions.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a contradiction-finding report written by an agent who read a
quarterly business report.

The quarterly report contains exactly one clear internal contradiction about Q3
revenue direction:
- The Executive Summary states: "Q3 revenue grew 12% over Q2, marking the second
  consecutive quarter of sequential growth."
- The Revenue Performance section states: "Q3 revenue came in below Q2, declining
  for the second straight quarter as macroeconomic headwinds dampened consumer
  discretionary spending."

These two statements directly contradict each other: one says Q3 revenue grew vs Q2;
the other says it declined vs Q2.

Score these axes, each a float from 0.0 to 1.0:
- correctness: does the report correctly identify the Q3 revenue contradiction
  (grew 12% vs declined below Q2)? Score 1.0 only if this specific contradiction
  is identified. Score 0.0 if it is missed entirely or if only fabricated
  contradictions are reported.
- solution_quality: does the report cite or quote both conflicting statements
  (the growth claim AND the decline claim)? Score higher when both sides of the
  contradiction are explicitly referenced.
- instruction_following: does the agent write to /app/contradictions.md with the
  contradiction(s) identified and both sides cited, as instructed?
- goal_adherence: does the report stay grounded in the actual document content,
  without inventing contradictions that are not present in the text?

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
        _zero("no /app/contradictions.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/contradictions.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nCONTRADICTIONS REPORT:\n{content}"}],
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
