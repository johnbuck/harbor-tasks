"""LLM-judge verifier for diagnose-from-logs-01.

Reads the agent's diagnosis, asks an Anthropic model to score it against a fixed
rubric, and writes multi-axis scores to /logs/verifier/reward.json.

Robust to SDK churn: uses the plain messages API and parses a JSON object out
of the reply rather than relying on structured-output features.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

TARGET = Path("/app/diagnosis.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a crash diagnosis written by an agent who read an incident log.

The incident log showed a Python web application crashing with:
    KeyError: 'user_id'
raised at this line inside the function handle_request:
    user = db.get_user(payload['user_id'])
The inbound request that triggered the crash had a JSON body of
{"action":"transfer","amount":250} — the 'user_id' key was absent from the payload.
The root cause is that handle_request accesses payload['user_id'] without first
checking whether the key exists, so any request missing that field crashes the handler.

Score these axes, each a float from 0.0 to 1.0:
- correctness: does the diagnosis correctly identify that handle_request raises
  KeyError: 'user_id' because it directly indexes a missing key in the request
  payload? Score 1.0 only if both the specific crash cause AND the missing-key
  reason are stated clearly.
- solution_quality: does the recommended fix address the root cause soundly?
  A good fix validates or defaults the key before use (e.g. payload.get('user_id'),
  checking for key presence, or returning an error early). Score higher for
  concrete, code-level suggestions.
- instruction_following: does the response include both required parts —
  (1) root cause and (2) recommended fix?
- goal_adherence: does the diagnosis stay focused on the actual incident in the
  log, without inventing causes not supported by the log?

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
        _zero("no /app/diagnosis.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/diagnosis.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nDIAGNOSIS:\n{content}"}],
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
