"""LLM-judge verifier for sub-agent-01.

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

TARGET = Path("/app/code-reviewer.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a Claude Code subagent definition file against a fixed brief.

The brief required ALL of:
1. The file begins with valid YAML frontmatter delimited by --- lines.
2. The frontmatter contains a "name:" field with a non-empty value.
3. The frontmatter contains a "description:" field whose value makes clear when
   this subagent should be invoked (i.e. for code review tasks).
4. After the closing --- there is a system prompt (body text) that defines a
   focused code-review role covering bugs, security, and style.
5. The system prompt is scoped to code review and does not try to be a
   general-purpose assistant.

Score these axes, each a float from 0.0 to 1.0:
- correctness: whether the file has valid YAML frontmatter with both "name" and
  "description" fields present and non-empty (1.0 = both present and valid).
- instruction_following: whether the file structure matches what was asked
  (frontmatter + body system prompt, written to the correct path).
- solution_quality: how focused, well-scoped, and useful the system prompt is
  as a code-review specialist role (not too broad, not too narrow).
- goal_adherence: whether the subagent is clearly about code review (bugs,
  security, style) and not some other topic.

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
        _zero("no /app/code-reviewer.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/code-reviewer.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nFILE CONTENTS:\n{content}"}],
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
