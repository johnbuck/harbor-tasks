"""LLM-judge verifier for email-copy-01.

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

TARGET = Path("/app/email.txt")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a product launch email against a fixed brief.

The brief required ALL of:
1. A subject line on the first line, prefixed exactly with "Subject: ".
2. An explicit mention of the product name "Lumen Plus".
3. At least two concrete benefits of upgrading.
4. The privacy angle (data never leaves the device).
5. A single, explicit call to action to upgrade.
Constraints: body under ~200 words; no fabricated statistics or fake quotes.

Score these axes, each a float from 0.0 to 1.0:
- correctness: fraction of the 5 required elements correctly present.
- instruction_following: adherence to the constraints (length, no fabrication,
  only the email written).
- solution_quality: how persuasive / well-written the email is.
- goal_adherence: how well it stays on-task (announce Lumen Plus, drive upgrades).

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
        _zero("no /app/email.txt produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/email.txt is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nEMAIL:\n{content}"}],
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
