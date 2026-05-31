#!/bin/bash
# Graded verifier for sub-agent-01.
#
# 10 specialist subagent files, each scored on 4 independent sub-checks:
#   (1) file exists with valid YAML frontmatter (--- ... ---)
#   (2) frontmatter `name:` matches the filename stem
#   (3) `description:` (in frontmatter) contains the required trigger keyword
#   (4) body (after frontmatter) is >=40 words, mentions the focus keyword,
#       AND contains a scope-limiting phrase (not a general-purpose assistant)
#
# reward = passed_subchecks / 40  (graded fraction; NOT binary).
# correctness = 1 iff all 40 pass.
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json, re, os

AGENTS = [
    # name,             trigger,       focus
    ("code-reviewer",     "review",      "bug"),
    ("security-auditor",  "security",    "vulnerability"),
    ("test-writer",       "test",        "coverage"),
    ("doc-writer",        "document",    "documentation"),
    ("refactorer",        "refactor",    "readability"),
    ("perf-profiler",     "performance", "latency"),
    ("dependency-auditor","dependency",  "version"),
    ("migration-planner", "migration",   "rollback"),
    ("api-designer",      "api",         "endpoint"),
    ("db-modeler",        "schema",      "index"),
]

SCOPE_PHRASES = ["not a general-purpose", "sole purpose", "only", "solely",
                 "nothing else", "single specialty", "redirect"]

passed = 0
total = 0
per_file = {}

def split_frontmatter(text):
    # Returns (frontmatter_str, body_str) or (None, None) if no valid block.
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, None
    return m.group(1), m.group(2)

for name, trigger, focus in AGENTS:
    path = f"/app/agents/{name}.md"
    checks = {"frontmatter": 0, "name": 0, "description": 0, "body": 0}
    text = ""
    if os.path.isfile(path):
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            text = ""
    fm, body = split_frontmatter(text)
    if fm is not None:
        checks["frontmatter"] = 1
        # (2) name: matches stem
        nm = re.search(r"^\s*name\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
        if nm and nm.group(1).strip().strip('"\'') == name:
            checks["name"] = 1
        # (3) description contains trigger keyword
        dm = re.search(r"^\s*description\s*:\s*(.*?)(?=^\s*\w+\s*:|\Z)",
                       fm, re.MULTILINE | re.DOTALL)
        desc = dm.group(1) if dm else ""
        if trigger.lower() in desc.lower():
            checks["description"] = 1
        # (4) body: >=40 words AND mentions focus AND has a scope-limiting phrase
        words = len(re.findall(r"\w+", body))
        has_focus = focus.lower() in body.lower()
        has_scope = any(p in body.lower() for p in SCOPE_PHRASES)
        if words >= 40 and has_focus and has_scope:
            checks["body"] = 1
    per_file[name] = checks
    passed += sum(checks.values())
    total += 4

reward = round(passed / total, 4) if total else 0.0
correctness = 1 if passed == total else 0
print(json.dumps({
    "reward": reward,
    "correctness": correctness,
    "subchecks_passed": passed,
    "subchecks_total": total,
}, indent=2))
PY
