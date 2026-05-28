"""LLM-judge verifier for restore-runbook-01.

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

TARGET = Path("/app/runbook.md")
REWARD = Path("/logs/verifier/reward.json")

RUBRIC = """\
You are grading a database restore runbook against a fixed setup description.

The setup: PostgreSQL 15 database "appdb" on "db.acme.internal", backed up
nightly via pg_dump, gzip-compressed, stored as appdb-YYYY-MM-DD.sql.gz in
s3://acme-backups/appdb/, 7-day retention, credentials in /root/.pgpass,
restore target host "restore.acme.internal", AWS CLI pre-configured.

The runbook must cover ALL FOUR phases:
1. Locate/choose the backup — finding the most recent file in the S3 bucket
   (e.g. aws s3 ls s3://acme-backups/appdb/ and picking the latest).
2. Retrieve the backup — downloading it from S3 to the restore host
   (e.g. aws s3 cp ...).
3. Restore the database — decompress (gunzip) and load into appdb using psql
   or pg_restore; must include creating the database/role if needed.
4. Verify the restore — at least one concrete check (e.g. psql row count,
   \dt listing, or application smoke test).

Score these axes, each a float from 0.0 to 1.0:
- correctness: fraction of the four phases correctly and technically soundly
  addressed; commands must be appropriate for a pg_dump + S3 setup.
- instruction_following: covers all four phases (locate, retrieve, restore,
  verify) as explicitly required.
- solution_quality: steps are ordered, concrete, and complete; a real engineer
  could execute this runbook without guessing.
- goal_adherence: the runbook matches the described setup (S3 + pg_dump +
  .pgpass) and does not invent infrastructure not mentioned there.

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
        _zero("no /app/runbook.md produced")
        return
    content = TARGET.read_text().strip()
    if not content:
        _zero("/app/runbook.md is empty")
        return

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=512,
        messages=[{"role": "user", "content": f"{RUBRIC}\n\nRUNBOOK:\n{content}"}],
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
