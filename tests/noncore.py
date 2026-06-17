"""Registry of the 21 active non-core tasks under remediation by
2026-06-16-noncore-task-remediation.

Shared by the offline s4 / hygiene / drift suites so the task list + grader
shape live in one place. ``shape`` is the grader's reward.json writer:

* ``rewardkit`` — ``tests/test.sh`` calls ``rewardkit ... --output reward.json``;
  the crash fallback is the ``|| echo '{"reward": 0.0}'`` form and the answer
  read + ``answer_present`` live in ``tests/reward.py``.
* ``heredoc``  — ``tests/test.sh`` builds reward.json via ``python3 - <<PY >
  reward.json``; the crash fallback is a post-heredoc ``[ -s reward.json ] ||
  echo`` guard and the answer read + weight-0 ``answer_present`` live inline.

Paths are RELATIVE to the repo root (``helpers.REPO_ROOT``).
"""
from __future__ import annotations

# id -> dict(grader=<test.sh>, reward=<reward.py|None>, shape, task_toml)
TASKS: dict[str, dict] = {
    "refactor-multi-file-01": dict(
        dir="tasks/code-editing/refactor-multi-file-01",
        grader="tasks/code-editing/refactor-multi-file-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "pr-diff-review-01": dict(
        dir="tasks/code-spec-review/pr-diff-review-01",
        grader="tasks/code-spec-review/pr-diff-review-01/tests/test.sh",
        reward="tasks/code-spec-review/pr-diff-review-01/tests/reward.py", shape="rewardkit"),
    "secret-scan-01": dict(
        dir="tasks/compliance-security/secret-scan-01",
        grader="tasks/compliance-security/secret-scan-01/tests/test.sh",
        reward="tasks/compliance-security/secret-scan-01/tests/reward.py", shape="rewardkit"),
    "multistep-context-fill-01": dict(
        dir="tasks/context-management/multistep-context-fill-01",
        grader="tasks/context-management/multistep-context-fill-01/steps/19-recall/tests/test.sh",
        reward="tasks/context-management/multistep-context-fill-01/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "multistep-context-fill-03": dict(
        dir="tasks/context-management/multistep-context-fill-03",
        grader="tasks/context-management/multistep-context-fill-03/steps/19-recall/tests/test.sh",
        reward="tasks/context-management/multistep-context-fill-03/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "context-rot-01": dict(
        dir="tasks/context-rot/context-rot-01",
        grader="tasks/context-rot/context-rot-01/steps/19-recall/tests/test.sh",
        reward="tasks/context-rot/context-rot-01/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "multistep-memory-conversational-02": dict(
        dir="tasks/conversation-persona/multistep-memory-conversational-02",
        grader="tasks/conversation-persona/multistep-memory-conversational-02/steps/06-recall/tests/test.sh",
        reward="tasks/conversation-persona/multistep-memory-conversational-02/steps/06-recall/tests/reward.py",
        shape="rewardkit"),
    "multistep-memory-conversational-03": dict(
        dir="tasks/conversation-persona/multistep-memory-conversational-03",
        grader="tasks/conversation-persona/multistep-memory-conversational-03/steps/07-recall/tests/test.sh",
        reward="tasks/conversation-persona/multistep-memory-conversational-03/steps/07-recall/tests/reward.py",
        shape="rewardkit"),
    "multistep-proactive-preference-01": dict(
        dir="tasks/conversation-persona/multistep-proactive-preference-01",
        grader="tasks/conversation-persona/multistep-proactive-preference-01/steps/04-announce/tests/test.sh",
        reward="tasks/conversation-persona/multistep-proactive-preference-01/steps/04-announce/tests/reward.py",
        shape="rewardkit"),
    "pandas-sql-from-nl-01": dict(
        dir="tasks/data-analytics/pandas-sql-from-nl-01",
        grader="tasks/data-analytics/pandas-sql-from-nl-01/tests/test.sh",
        reward="tasks/data-analytics/pandas-sql-from-nl-01/tests/reward.py", shape="rewardkit"),
    "find-contradictions-01": dict(
        dir="tasks/insights-research/find-contradictions-01",
        grader="tasks/insights-research/find-contradictions-01/tests/test.sh",
        reward="tasks/insights-research/find-contradictions-01/tests/reward.py", shape="rewardkit"),
    "dep-bump-breaking-01": dict(
        dir="tasks/migration/dep-bump-breaking-01",
        grader="tasks/migration/dep-bump-breaking-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "diagnose-from-logs-01": dict(
        dir="tasks/ops-debugging/diagnose-from-logs-01",
        grader="tasks/ops-debugging/diagnose-from-logs-01/tests/test.sh",
        reward="tasks/ops-debugging/diagnose-from-logs-01/tests/reward.py", shape="rewardkit"),
    "shell-pipeline-01": dict(
        dir="tasks/ops-debugging/shell-pipeline-01",
        grader="tasks/ops-debugging/shell-pipeline-01/tests/test.sh",
        reward="tasks/ops-debugging/shell-pipeline-01/tests/reward.py", shape="rewardkit"),
    "prompt-injection-resistance-01": dict(
        dir="tasks/real-world-workflows/prompt-injection-resistance-01",
        grader="tasks/real-world-workflows/prompt-injection-resistance-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "schedule-meeting-from-name-01": dict(
        dir="tasks/real-world-workflows/schedule-meeting-from-name-01",
        grader="tasks/real-world-workflows/schedule-meeting-from-name-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "agentic-research-with-memory-01": dict(
        dir="tasks/research-rag/agentic-research-with-memory-01",
        grader="tasks/research-rag/agentic-research-with-memory-01/tests/test.sh",
        reward="tasks/research-rag/agentic-research-with-memory-01/tests/reward.py", shape="rewardkit"),
    "factual-lookup-cited-01": dict(
        dir="tasks/research-rag/factual-lookup-cited-01",
        grader="tasks/research-rag/factual-lookup-cited-01/tests/test.sh",
        reward="tasks/research-rag/factual-lookup-cited-01/tests/reward.py", shape="rewardkit"),
    "unit-tests-01": dict(
        dir="tasks/test-authoring/unit-tests-01",
        grader="tasks/test-authoring/unit-tests-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "browser-find-fact-01": dict(
        dir="tasks/tool-orchestration/browser-find-fact-01",
        grader="tasks/tool-orchestration/browser-find-fact-01/tests/test.sh",
        reward=None, shape="heredoc"),
    "tool-selection-01": dict(
        dir="tasks/tool-orchestration/tool-selection-01",
        grader="tasks/tool-orchestration/tool-selection-01/tests/test.sh",
        reward="tasks/tool-orchestration/tool-selection-01/tests/reward.py", shape="rewardkit"),
}

assert len(TASKS) == 21, len(TASKS)

REWARDKIT = [k for k, v in TASKS.items() if v["shape"] == "rewardkit"]
HEREDOC = [k for k, v in TASKS.items() if v["shape"] == "heredoc"]


def task_toml(rel_dir: str) -> str:
    return f"{rel_dir}/task.toml"
