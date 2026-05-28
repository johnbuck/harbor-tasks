"""LLM-judge verifier for pr-diff-review-01.

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

TARGET = Path("/app/review.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a code review written in response to a pull request diff.

The diff introduced an endpoint that looks up a user by username. The critical
security bug in the diff is a SQL injection vulnerability: the code builds the
SQL query using an f-string that interpolates user-supplied input directly:
    cursor.execute(f"SELECT ... WHERE username = '{username}'")
The correct fix is to use a parameterized query:
    cursor.execute("SELECT ... WHERE username = ?", (username,))

The review must:
1. Identify the SQL injection as the key security issue.
2. Recommend a concrete fix (parameterized query / prepared statement).
3. Not merely say "LGTM" or approve the change without flagging the vulnerability.
4. Not pad the review with excessive trivial nitpicks unrelated to the real issue
   (minor style, whitespace, docstring wording, etc. should not dominate the review).

Score these axes, each a float from 0.0 to 1.0:
- correctness: the review correctly identifies the SQL injection vulnerability as
  the primary issue; score 0.0 if the vulnerability is not identified at all,
  1.0 if it is clearly identified and accurately described.
- instruction_following: recommends a concrete fix (parameterized query or
  equivalent) and does not rubber-stamp the diff; score 0.0 if the review
  approves without reservation.
- solution_quality: focused on the real issue; penalize reviews that bury the
  SQL injection under a pile of trivial nitpicks (variable naming, whitespace,
  docstring style) where the security issue is not the clear priority.
- goal_adherence: reviews the actual diff provided, stays on topic.

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
        _zero("no /app/review.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/review.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nREVIEW:\n{content}"}],
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
