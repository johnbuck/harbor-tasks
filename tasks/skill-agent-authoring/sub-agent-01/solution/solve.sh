#!/bin/bash
# Reference solution — authors all 10 specialist subagent files.
set -e
mkdir -p /app/agents

emit() {
  # $1=name $2=trigger-phrase $3=focus-keyword
  cat > "/app/agents/$1.md" <<EOF
---
name: $1
description: >
  Invoke this $1 subagent when the user wants to $2 their work. It handles
  $2-related requests and nothing else.
---

You are the $1 specialist. Your sole purpose is to handle $2 tasks for the
user, focusing tightly on $3 concerns. You are not a general-purpose assistant:
if asked to do anything outside your specialty you politely decline and redirect
to your purpose. For every request, produce structured, actionable findings that
center on $3 and the user's $2 goal, and stop there.
EOF
}

emit code-reviewer      "review"      "bug"
emit security-auditor   "security"    "vulnerability"
emit test-writer        "test"        "coverage"
emit doc-writer         "document"    "documentation"
emit refactorer         "refactor"    "readability"
emit perf-profiler      "performance" "latency"
emit dependency-auditor "dependency"  "version"
emit migration-planner  "migration"   "rollback"
emit api-designer       "api"         "endpoint"
emit db-modeler         "schema"      "index"
