"""rewardkit grader for api-contract-01 — OpenAPI 3.0 Todo contract.

16 equal-weight criteria over the agent's /app/openapi.yaml, one per rule in the
instruction. reward = satisfied / 16 (rewardkit weighted_mean of equal-weight
binary criteria); the per-criterion breakdown lands in reward-details.json,
reward.json stays {"reward": <float>} (Hard Rule #2). Replaces the prior bespoke
grade.py — same requirements, structured + flat-reward-guaranteed by rewardkit.
"""
from functools import lru_cache
from pathlib import Path

import yaml
import rewardkit as rk


@lru_cache(maxsize=4)
def _evaluate(workspace_str: str) -> tuple:
    """Parse the agent's openapi.yaml and return {criterion_key: bool}.

    Cached so all 16 criteria share one parse. Returns a tuple of (key, value)
    pairs (hashable for the cache); callers wrap it back into a dict.
    """
    R = {k: False for k in (
        "openapi3", "get_list_200", "get_list_array_ref", "post_201",
        "post_201_ref_todo", "post_requestbody", "create_input_no_id",
        "post_400", "post_400_ref_error", "get_item_200_ref", "get_item_404",
        "delete_204", "delete_404", "id_path_param", "todo_schema",
        "error_schema")}

    target = Path(workspace_str) / "openapi.yaml"
    if not target.exists() or not target.read_text().strip():
        return tuple(R.items())
    try:
        spec = yaml.safe_load(target.read_text())
    except Exception:
        return tuple(R.items())
    if not isinstance(spec, dict):
        return tuple(R.items())

    def ref_name(node):
        if isinstance(node, dict) and isinstance(node.get("$ref"), str):
            return node["$ref"].rsplit("/", 1)[-1].lower()
        return None

    def json_schema(holder):
        """The application/json schema node of a response or requestBody."""
        if not isinstance(holder, dict):
            return None
        content = holder.get("content")
        if not isinstance(content, dict):
            return None
        for ctype, media in content.items():
            if "json" in str(ctype).lower() and isinstance(media, dict):
                return media.get("schema")
        return None

    def op_response(op, code):
        if not isinstance(op, dict):
            return None
        responses = op.get("responses") or {}
        return responses.get(code) or responses.get(int(code))

    paths = spec.get("paths") if isinstance(spec.get("paths"), dict) else {}
    schemas = {}
    comps = spec.get("components")
    if isinstance(comps, dict) and isinstance(comps.get("schemas"), dict):
        schemas = comps["schemas"]

    def find_schema(want):
        for name, sch in schemas.items():
            if name.lower() == want:
                return sch
        return None

    todo_sch = find_schema("todo")
    err_sch = find_schema("error")

    # /todos (collection) and /todos/{id} (item) operations, case-insensitive
    coll = {}
    if isinstance(paths.get("/todos"), dict):
        coll = {m.lower(): op for m, op in paths["/todos"].items()}
    item, item_raw = {}, {}
    for key, val in paths.items():
        if key.startswith("/todos/{") and key.endswith("}") and isinstance(val, dict):
            item_raw = val
            item = {m.lower(): op for m, op in val.items()}
            break

    get_coll, post_coll = coll.get("get"), coll.get("post")
    get_item, del_item = item.get("get"), item.get("delete")

    # S1 — OpenAPI 3.x
    R["openapi3"] = str(spec.get("openapi", "")).startswith("3.")

    # S2/S3 — GET /todos -> 200, array of $ref Todo
    if isinstance(get_coll, dict) and op_response(get_coll, "200") is not None:
        R["get_list_200"] = True
        sch = json_schema(op_response(get_coll, "200"))
        if (isinstance(sch, dict) and str(sch.get("type", "")).lower() == "array"
                and ref_name(sch.get("items")) == "todo"):
            R["get_list_array_ref"] = True

    # S4/S5 — POST /todos -> 201 referencing Todo
    if isinstance(post_coll, dict) and op_response(post_coll, "201") is not None:
        R["post_201"] = True
        if ref_name(json_schema(op_response(post_coll, "201"))) == "todo":
            R["post_201_ref_todo"] = True

    # S6 — POST requestBody (required: true) referencing a schema
    body_ref = None
    body = post_coll.get("requestBody") if isinstance(post_coll, dict) else None
    if isinstance(body, dict) and body.get("required") is True:
        body_ref = ref_name(json_schema(body))
        if body_ref:
            R["post_requestbody"] = True

    # S7 — create input must NOT require the client to supply `id`
    if body_ref:
        if body_ref != "todo":
            R["create_input_no_id"] = True            # a distinct create schema
        elif isinstance(todo_sch, dict):
            req = [str(x).lower() for x in (todo_sch.get("required") or [])]
            R["create_input_no_id"] = "id" not in req  # reused Todo w/o required id

    # S8/S9 — POST 400 referencing Error
    if isinstance(post_coll, dict) and op_response(post_coll, "400") is not None:
        R["post_400"] = True
        if ref_name(json_schema(op_response(post_coll, "400"))) == "error":
            R["post_400_ref_error"] = True

    # S10/S11 — GET /todos/{id} -> 200 ref Todo, 404
    if isinstance(get_item, dict):
        if ref_name(json_schema(op_response(get_item, "200"))) == "todo":
            R["get_item_200_ref"] = True
        if op_response(get_item, "404") is not None:
            R["get_item_404"] = True

    # S12/S13 — DELETE /todos/{id} -> 204, 404
    if isinstance(del_item, dict):
        if op_response(del_item, "204") is not None:
            R["delete_204"] = True
        if op_response(del_item, "404") is not None:
            R["delete_404"] = True

    # S14 — {id} path param (in: path, required, integer) on both item ops
    def has_id_param(op):
        params = []
        if isinstance(item_raw.get("parameters"), list):
            params += item_raw["parameters"]
        if isinstance(op, dict) and isinstance(op.get("parameters"), list):
            params += op["parameters"]
        for p in params:
            if (isinstance(p, dict) and str(p.get("in", "")).lower() == "path"
                    and p.get("required") is True
                    and str((p.get("schema") or {}).get("type", "")).lower() == "integer"):
                return True
        return False
    R["id_path_param"] = (isinstance(get_item, dict) and has_id_param(get_item)
                          and isinstance(del_item, dict) and has_id_param(del_item))

    # S15 — Todo schema: id/title/done present (typed) + all required
    if isinstance(todo_sch, dict):
        props = todo_sch.get("properties") or {}
        types = {k.lower(): str((v or {}).get("type", "")).lower()
                 for k, v in props.items()} if isinstance(props, dict) else {}
        req = {str(x).lower() for x in (todo_sch.get("required") or [])}
        R["todo_schema"] = (types.get("id") == "integer"
                            and types.get("title") == "string"
                            and types.get("done") == "boolean"
                            and {"id", "title", "done"} <= req)

    # S16 — Error schema with a `message` property
    if isinstance(err_sch, dict):
        eprops = err_sch.get("properties") or {}
        R["error_schema"] = isinstance(eprops, dict) and any(
            k.lower() == "message" for k in eprops)

    return tuple(R.items())


# 16 criteria, one per rule. Same key order as _evaluate; the label is what shows
# in reward-details.json / `harbor view`.
CRITERIA = [
    ("openapi3", "OpenAPI version is 3.x"),
    ("get_list_200", "GET /todos returns 200"),
    ("get_list_array_ref", "GET /todos 200 is an array of $ref Todo"),
    ("post_201", "POST /todos returns 201"),
    ("post_201_ref_todo", "POST /todos 201 body $refs Todo"),
    ("post_requestbody", "POST /todos has a required requestBody $ref"),
    ("create_input_no_id", "create input does not require client-supplied id"),
    ("post_400", "POST /todos declares a 400 response"),
    ("post_400_ref_error", "POST /todos 400 body $refs Error"),
    ("get_item_200_ref", "GET /todos/{id} 200 $refs Todo"),
    ("get_item_404", "GET /todos/{id} declares a 404"),
    ("delete_204", "DELETE /todos/{id} returns 204"),
    ("delete_404", "DELETE /todos/{id} declares a 404"),
    ("id_path_param", "{id} path param declared (in:path, required, integer)"),
    ("todo_schema", "Todo schema has id/title/done, all required"),
    ("error_schema", "Error schema has a message property"),
]


@rk.criterion(description="{label}")
def rule(workspace: Path, key: str, label: str) -> bool:
    return dict(_evaluate(str(workspace))).get(key, False)


for _key, _label in CRITERIA:
    rk.rule(_key, _label)
