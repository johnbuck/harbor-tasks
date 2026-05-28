"""LLM-judge verifier for tool-selection-01.

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

TARGET = Path("/app/plan.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a tool-selection plan written in response to a task.

The task was: "find the current weather in Tokyo right now."
The available tools were:
- web_search — queries a live search engine, can retrieve current external data.
- calculator — evaluates math expressions.
- file_reader — reads local files.
- sql_query — queries a local database.

The only correct answer is `web_search`. It is the only tool that can access
live, external, real-time data from the internet. The other three tools
(calculator, file_reader, sql_query) operate on local resources and have no
ability to retrieve current weather or any external live data.

Score these axes, each a float from 0.0 to 1.0:
- correctness: 1.0 if and only if the plan selects `web_search` as the chosen
  tool; 0.0 if any other tool is selected. This is binary.
- goal_adherence: the justification is grounded in the task requirement (live,
  external, real-time data about current weather); score lower if the reasoning
  ignores why the other tools are inappropriate.
- solution_quality: the reasoning is concise and sound; does not pad with
  irrelevant content; correctly explains why the other tools cannot accomplish
  this task.
- instruction_following: picks exactly one tool and provides a written
  justification; score lower if multiple tools are chosen or no justification
  is given.

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
        _zero("no /app/plan.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/plan.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nPLAN:\n{content}"}],
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
