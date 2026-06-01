"""Deterministic, LLM-free graded verifier for api-contract-01 (medium).

Grades each part of the OpenAPI contract independently. Every endpoint /
status-code / schema rule that is correct earns one point. reward is the
fraction satisfied; correctness is 1 only when ALL sub-criteria pass.

Sub-criteria (N=16):
  S1  openapi version is 3.x
  S2  GET /todos exists and returns 200
  S3  GET /todos 200 body is an ARRAY whose items $ref the Todo schema
  S4  POST /todos exists and returns 201
  S5  POST /todos 201 body $ref's the Todo schema
  S6  POST /todos declares a requestBody (required: true) that $ref's a schema
  S7  POST /todos request schema does NOT require the client to supply `id`
      (edge case: server assigns id — reusing full Todo, which requires id, is
      wrong). Satisfied if the body references a schema other than Todo, OR a
      Todo schema whose `required` list omits id.
  S8  POST /todos declares a 400 (validation-error) response  [edge case]
  S9  the 400 response body $ref's the Error schema                [edge case]
  S10 GET /todos/{id} exists and returns 200 referencing Todo
  S11 GET /todos/{id} declares a 404 response                      [edge case]
  S12 DELETE /todos/{id} exists and returns 204 (no content)
  S13 DELETE /todos/{id} declares a 404 response                   [edge case]
  S14 the {id} path parameter is declared (in: path, required: true, integer)
      on the /todos/{id} operations
  S15 Todo schema under components.schemas has id(integer)/title(string)/
      done(boolean) and lists all three as required
  S16 an Error schema exists under components.schemas with a `message` property

reward = round(satisfied / 16, 4); correctness = 1 iff satisfied == 16.

reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
"""

import json
import re
from pathlib import Path

import yaml

TARGET = Path("/app/openapi.yaml")
REWARD = Path("/logs/verifier/reward.json")
N = 16


def _zero(reason: str) -> None:
    REWARD.write_text(json.dumps(
        {"reward": 0.0, "correctness": 0, "satisfied": 0, "n_checks": N},
        indent=2))
    print(f"reward 0.0 — {reason}")


def _ref_name(node):
    """Return the schema name a $ref points at, or None."""
    if isinstance(node, dict) and isinstance(node.get("$ref"), str):
        return node["$ref"].rsplit("/", 1)[-1]
    return None


def _json_schema(resp_or_body):
    """Pull the application/json schema node out of a response/requestBody."""
    if not isinstance(resp_or_body, dict):
        return None
    content = resp_or_body.get("content")
    if not isinstance(content, dict):
        return None
    for ctype, media in content.items():
        if "json" in str(ctype).lower() and isinstance(media, dict):
            return media.get("schema")
    return None


def _find_schema(schemas, want):
    for name, sch in schemas.items():
        if name.lower() == want:
            return name, sch
    return None, None


def main() -> None:
    if not TARGET.exists() or not TARGET.read_text().strip():
        _zero("no /app/openapi.yaml produced")
        return
    try:
        spec = yaml.safe_load(TARGET.read_text())
    except Exception as e:
        _zero(f"YAML parse error: {e}")
        return
    if not isinstance(spec, dict):
        _zero("top-level YAML is not a mapping")
        return

    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        paths = {}
    schemas = ((spec.get("components") or {}).get("schemas")) or {}
    if not isinstance(schemas, dict):
        schemas = {}

    # locate the collection + item path objects (case-insensitive methods)
    coll = {k.lower(): v for k, v in (paths.get("/todos") or {}).items()
            if isinstance(paths.get("/todos"), dict)}
    item = {}
    item_raw = {}
    for k, v in paths.items():
        if re.fullmatch(r"/todos/\{[^}]+\}", k) and isinstance(v, dict):
            item_raw = v
            item = {m.lower(): op for m, op in v.items()}
            break

    todo_name, todo_sch = _find_schema(schemas, "todo")
    err_name, err_sch = _find_schema(schemas, "error")

    def resp(op, code):
        if not isinstance(op, dict):
            return None
        r = op.get("responses") or {}
        return r.get(code) or r.get(int(code) if str(code).isdigit() else code)

    R = {}

    # S1 openapi 3.x
    R["s1_openapi3"] = str(spec.get("openapi", "")).startswith("3.")

    # S2 GET /todos -> 200
    get_coll = coll.get("get")
    R["s2_get_todos_200"] = isinstance(get_coll, dict) and resp(get_coll, "200") is not None

    # S3 GET /todos 200 body is array of $ref Todo
    s3 = False
    sch = _json_schema(resp(get_coll, "200")) if isinstance(get_coll, dict) else None
    if isinstance(sch, dict) and str(sch.get("type", "")).lower() == "array":
        if _ref_name(sch.get("items")) and _ref_name(sch["items"]).lower() == "todo":
            s3 = True
    R["s3_get_todos_array_ref"] = s3

    # S4 POST /todos -> 201
    post_coll = coll.get("post")
    R["s4_post_todos_201"] = isinstance(post_coll, dict) and resp(post_coll, "201") is not None

    # S5 POST 201 body $ref Todo
    s5 = False
    psch = _json_schema(resp(post_coll, "201")) if isinstance(post_coll, dict) else None
    if _ref_name(psch) and _ref_name(psch).lower() == "todo":
        s5 = True
    R["s5_post_201_ref_todo"] = s5

    # S6 POST requestBody required:true with $ref'd schema
    s6 = False
    body = post_coll.get("requestBody") if isinstance(post_coll, dict) else None
    body_ref = None
    if isinstance(body, dict) and body.get("required") is True:
        bsch = _json_schema(body)
        body_ref = _ref_name(bsch)
        if body_ref:
            s6 = True
    R["s6_post_requestbody"] = s6

    # S7 create-input must not require client to supply id  [edge case]
    s7 = False
    if body_ref:
        if body_ref.lower() != "todo":
            s7 = True  # separate create-input schema
        else:
            req = (todo_sch or {}).get("required") if isinstance(todo_sch, dict) else None
            if isinstance(req, list) and "id" not in [str(x).lower() for x in req]:
                s7 = True  # reused Todo but id not required
    R["s7_create_input_no_id"] = s7

    # S8 POST 400 response  [edge case]
    R["s8_post_400"] = isinstance(post_coll, dict) and resp(post_coll, "400") is not None

    # S9 400 body $ref Error  [edge case]
    s9 = False
    e400 = _json_schema(resp(post_coll, "400")) if isinstance(post_coll, dict) else None
    if _ref_name(e400) and _ref_name(e400).lower() == "error":
        s9 = True
    R["s9_400_ref_error"] = s9

    # S10 GET /todos/{id} -> 200 ref Todo
    get_item = item.get("get")
    s10 = False
    if isinstance(get_item, dict) and resp(get_item, "200") is not None:
        gsch = _json_schema(resp(get_item, "200"))
        if _ref_name(gsch) and _ref_name(gsch).lower() == "todo":
            s10 = True
    R["s10_get_item_200_ref"] = s10

    # S11 GET item 404  [edge case]
    R["s11_get_item_404"] = isinstance(get_item, dict) and resp(get_item, "404") is not None

    # S12 DELETE item -> 204
    del_item = item.get("delete")
    R["s12_delete_204"] = isinstance(del_item, dict) and resp(del_item, "204") is not None

    # S13 DELETE item 404  [edge case]
    R["s13_delete_404"] = isinstance(del_item, dict) and resp(del_item, "404") is not None

    # S14 {id} path param declared (in:path, required, integer)
    def has_id_param(op):
        params = []
        if isinstance(item_raw, dict) and isinstance(item_raw.get("parameters"), list):
            params += item_raw["parameters"]
        if isinstance(op, dict) and isinstance(op.get("parameters"), list):
            params += op["parameters"]
        for p in params:
            if not isinstance(p, dict):
                continue
            if (str(p.get("in", "")).lower() == "path"
                    and p.get("required") is True
                    and str((p.get("schema") or {}).get("type", "")).lower() == "integer"):
                return True
        return False
    R["s14_id_param"] = (isinstance(get_item, dict) and has_id_param(get_item)
                         and isinstance(del_item, dict) and has_id_param(del_item))

    # S15 Todo schema id/title/done all present + required
    s15 = False
    if isinstance(todo_sch, dict):
        props = todo_sch.get("properties") or {}
        types = {k.lower(): str((v or {}).get("type", "")).lower()
                 for k, v in props.items() if isinstance(props, dict)}
        req = [str(x).lower() for x in (todo_sch.get("required") or [])]
        if (types.get("id") == "integer" and types.get("title") == "string"
                and types.get("done") == "boolean"
                and {"id", "title", "done"}.issubset(set(req))):
            s15 = True
    R["s15_todo_schema"] = s15

    # S16 Error schema with message property
    s16 = False
    if isinstance(err_sch, dict):
        eprops = err_sch.get("properties") or {}
        if isinstance(eprops, dict) and any(k.lower() == "message" for k in eprops):
            s16 = True
    R["s16_error_schema"] = s16

    satisfied = sum(1 for v in R.values() if v)
    reward = round(satisfied / N, 4)
    correctness = 1 if satisfied == N else 0

    out = {"reward": reward, "correctness": correctness,
           "satisfied": satisfied, "n_checks": N}
    out.update({f"ok_{k}": int(bool(v)) for k, v in R.items()})
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
