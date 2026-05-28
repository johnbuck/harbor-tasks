"""Mixed grader for api-contract-01.

correctness + instruction_following come from a deterministic structural check
of the OpenAPI YAML. solution_quality + goal_adherence come from an LLM judge.
reward = correctness.
"""

import json
import os
import re
from pathlib import Path

import yaml
from anthropic import Anthropic

TARGET = Path("/app/openapi.yaml")
REWARD = Path("/logs/verifier/reward.json")
AXES = ["correctness", "instruction_following", "solution_quality", "goal_adherence"]


def structural_check(spec: dict) -> tuple[float, float]:
    """Return (correctness, instruction_following) as 0/1 floats."""
    try:
        ok = True
        ok &= str(spec.get("openapi", "")).startswith("3.")
        paths = spec.get("paths", {}) or {}
        todos = {k.lower(): v for k, v in (paths.get("/todos", {}) or {}).items()}
        ok &= "get" in todos and "post" in todos
        # path key may be /todos/{id} or similar templated id
        id_path = None
        for k in paths:
            if re.fullmatch(r"/todos/\{[^}]+\}", k):
                id_path = {m.lower() for m in (paths[k] or {})}
                break
        ok &= id_path is not None and "get" in id_path and "delete" in id_path
        schemas = (spec.get("components", {}) or {}).get("schemas", {}) or {}
        todo = None
        for name, sch in schemas.items():
            if name.lower() == "todo":
                todo = sch
                break
        if todo is None and schemas:
            todo = next(iter(schemas.values()))
        props = (todo or {}).get("properties", {}) or {}
        ok &= {"id", "title", "done"}.issubset(set(props.keys()))
        return (1.0 if ok else 0.0), 1.0
    except Exception:
        return 0.0, 0.0


def judge_quality(raw: str) -> tuple[float, float]:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    rubric = (
        "You are grading the design quality of an OpenAPI 3 contract for a Todo "
        "API (GET/POST /todos, GET/DELETE /todos/{id}, a Todo schema with id/"
        "title/done). Score two axes as floats 0.0-1.0:\n"
        "- solution_quality: are response codes sensible, schemas $ref'd, the "
        "contract clean and complete?\n"
        "- goal_adherence: does it model exactly this Todo API, no scope creep?\n"
        'Respond with ONLY JSON: {"solution_quality": <f>, "goal_adherence": <f>}'
    )
    resp = client.messages.create(
        model=os.environ["MODEL_NAME"],
        max_tokens=300,
        messages=[{"role": "user", "content": f"{rubric}\n\nSPEC:\n{raw}"}],
    )
    m = re.search(r"\{.*\}", resp.content[0].text, re.DOTALL)
    if not m:
        return 0.0, 0.0
    d = json.JSONDecoder().raw_decode(m.group(0))[0]

    def clamp(x):
        try:
            return max(0.0, min(1.0, float(x)))
        except (TypeError, ValueError):
            return 0.0

    return clamp(d.get("solution_quality")), clamp(d.get("goal_adherence"))


def main() -> None:
    if not TARGET.exists() or not TARGET.read_text().strip():
        REWARD.write_text(json.dumps(
            {a: 0.0 for a in AXES} | {"reward": 0.0}, indent=2))
        return
    raw = TARGET.read_text()
    try:
        spec = yaml.safe_load(raw)
    except Exception as e:
        REWARD.write_text(json.dumps(
            {a: 0.0 for a in AXES} | {"reward": 0.0}, indent=2))
        return

    correctness, instr = structural_check(spec if isinstance(spec, dict) else {})
    quality, goal = judge_quality(raw)
    out = {
        "correctness": correctness,
        "instruction_following": instr,
        "solution_quality": quality,
        "goal_adherence": goal,
        "reward": correctness,
    }
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
