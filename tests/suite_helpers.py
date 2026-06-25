"""Registry of the 21 suite tasks under remediation by
2026-06-16-noncore-task-remediation.

Shared by the offline s4 / hygiene / drift suites so the task list + grader
shape live in one place. ``shape`` is the grader's reward.json writer:

* ``rewardkit`` — ``tests/test.sh`` calls ``rewardkit ... --output reward.json``;
  the crash fallback is the ``|| echo '{"reward": 0.0}'`` form and the answer
  read + ``answer_present`` live in ``tests/reward.py``.
* ``heredoc``  — ``tests/test.sh`` builds reward.json via ``python3 - <<PY >
  reward.json``; the crash fallback is a post-heredoc ``[ -s reward.json ] ||
  echo`` guard and the answer read + weight-0 ``answer_present`` live inline.

The suite-wide direction is "everything rewardkit"; as of the 2026-06-25
conversion pass ALL 21 tasks are rewardkit. The ``heredoc`` shape is retained
above for the s4 parametrization but currently has no members.

Keys are the CURRENT task identity (the renamed task dir basename); the prior
``<shape>-NN`` ids were retired by the 2026-06-16 rename pass. Paths are RELATIVE
to the repo root (``helpers.REPO_ROOT``).
"""
from __future__ import annotations

# id -> dict(dir, grader=<test.sh>, reward=<reward.py|None>, shape)
TASKS: dict[str, dict] = {
    "geometry-polymorphism-refactor": dict(
        dir="tasks/code-editing/geometry-polymorphism-refactor",
        grader="tasks/code-editing/geometry-polymorphism-refactor/tests/test.sh",
        reward="tasks/code-editing/geometry-polymorphism-refactor/tests/reward.py", shape="rewardkit"),
    "security-code-review": dict(
        dir="tasks/code-spec-review/security-code-review",
        grader="tasks/code-spec-review/security-code-review/tests/test.sh",
        reward="tasks/code-spec-review/security-code-review/tests/reward.py", shape="rewardkit"),
    "credential-leak-detection": dict(
        dir="tasks/compliance-security/credential-leak-detection",
        grader="tasks/compliance-security/credential-leak-detection/tests/test.sh",
        reward="tasks/compliance-security/credential-leak-detection/tests/reward.py", shape="rewardkit"),
    "track-project-across-context-overflow": dict(
        dir="tasks/context-management/track-project-across-context-overflow",
        grader="tasks/context-management/track-project-across-context-overflow/steps/19-recall/tests/test.sh",
        reward="tasks/context-management/track-project-across-context-overflow/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "separate-two-parallel-projects": dict(
        dir="tasks/context-management/separate-two-parallel-projects",
        grader="tasks/context-management/separate-two-parallel-projects/steps/19-recall/tests/test.sh",
        reward="tasks/context-management/separate-two-parallel-projects/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "retain-details-across-long-survey": dict(
        dir="tasks/context-rot/retain-details-across-long-survey",
        grader="tasks/context-rot/retain-details-across-long-survey/steps/19-recall/tests/test.sh",
        reward="tasks/context-rot/retain-details-across-long-survey/steps/19-recall/tests/reward.py",
        shape="rewardkit"),
    "recall-details-across-task-switching": dict(
        dir="tasks/conversation-persona/recall-details-across-task-switching",
        grader="tasks/conversation-persona/recall-details-across-task-switching/steps/06-recall/tests/test.sh",
        reward="tasks/conversation-persona/recall-details-across-task-switching/steps/06-recall/tests/reward.py",
        shape="rewardkit"),
    "recall-details-under-high-load": dict(
        dir="tasks/conversation-persona/recall-details-under-high-load",
        grader="tasks/conversation-persona/recall-details-under-high-load/steps/07-recall/tests/test.sh",
        reward="tasks/conversation-persona/recall-details-under-high-load/steps/07-recall/tests/reward.py",
        shape="rewardkit"),
    "apply-standing-preferences-unprompted": dict(
        dir="tasks/conversation-persona/apply-standing-preferences-unprompted",
        grader="tasks/conversation-persona/apply-standing-preferences-unprompted/steps/04-announce/tests/test.sh",
        reward="tasks/conversation-persona/apply-standing-preferences-unprompted/steps/04-announce/tests/reward.py",
        shape="rewardkit"),
    "analyze-sales-data": dict(
        dir="tasks/data-analytics/analyze-sales-data",
        grader="tasks/data-analytics/analyze-sales-data/tests/test.sh",
        reward="tasks/data-analytics/analyze-sales-data/tests/reward.py", shape="rewardkit"),
    "audit-report-contradictions": dict(
        dir="tasks/insights-research/audit-report-contradictions",
        grader="tasks/insights-research/audit-report-contradictions/tests/test.sh",
        reward="tasks/insights-research/audit-report-contradictions/tests/reward.py", shape="rewardkit"),
    "pydantic-v2-migration": dict(
        dir="tasks/migration/pydantic-v2-migration",
        grader="tasks/migration/pydantic-v2-migration/tests/test.sh",
        reward="tasks/migration/pydantic-v2-migration/tests/reward.py", shape="rewardkit"),
    "http-outage-root-cause-from-logs": dict(
        dir="tasks/ops-debugging/http-outage-root-cause-from-logs",
        grader="tasks/ops-debugging/http-outage-root-cause-from-logs/tests/test.sh",
        reward="tasks/ops-debugging/http-outage-root-cause-from-logs/tests/reward.py", shape="rewardkit"),
    "log-analytics-with-tie-breaks": dict(
        dir="tasks/ops-debugging/log-analytics-with-tie-breaks",
        grader="tasks/ops-debugging/log-analytics-with-tie-breaks/tests/test.sh",
        reward="tasks/ops-debugging/log-analytics-with-tie-breaks/tests/reward.py", shape="rewardkit"),
    "summarize-support-emails-safely": dict(
        dir="tasks/real-world-workflows/summarize-support-emails-safely",
        grader="tasks/real-world-workflows/summarize-support-emails-safely/tests/test.sh",
        reward="tasks/real-world-workflows/summarize-support-emails-safely/tests/reward.py", shape="rewardkit"),
    "book-meeting-with-contact": dict(
        dir="tasks/real-world-workflows/book-meeting-with-contact",
        grader="tasks/real-world-workflows/book-meeting-with-contact/tests/test.sh",
        reward="tasks/real-world-workflows/book-meeting-with-contact/tests/reward.py", shape="rewardkit"),
    "research-org-profile-cited": dict(
        dir="tasks/research-rag/research-org-profile-cited",
        grader="tasks/research-rag/research-org-profile-cited/tests/test.sh",
        reward="tasks/research-rag/research-org-profile-cited/tests/reward.py", shape="rewardkit"),
    "verify-company-facts-cited": dict(
        dir="tasks/research-rag/verify-company-facts-cited",
        grader="tasks/research-rag/verify-company-facts-cited/tests/test.sh",
        reward="tasks/research-rag/verify-company-facts-cited/tests/reward.py", shape="rewardkit"),
    "comprehensive-unit-tests": dict(
        dir="tasks/test-authoring/comprehensive-unit-tests",
        grader="tasks/test-authoring/comprehensive-unit-tests/tests/test.sh",
        reward="tasks/test-authoring/comprehensive-unit-tests/tests/reward/reward.py", shape="rewardkit"),
    "web-research-multi-page": dict(
        dir="tasks/tool-orchestration/web-research-multi-page",
        grader="tasks/tool-orchestration/web-research-multi-page/tests/test.sh",
        reward="tasks/tool-orchestration/web-research-multi-page/tests/reward.py", shape="rewardkit"),
    "multi-goal-tool-routing": dict(
        dir="tasks/tool-orchestration/multi-goal-tool-routing",
        grader="tasks/tool-orchestration/multi-goal-tool-routing/tests/test.sh",
        reward="tasks/tool-orchestration/multi-goal-tool-routing/tests/reward.py", shape="rewardkit"),
}

assert len(TASKS) == 21, len(TASKS)

REWARDKIT = [k for k, v in TASKS.items() if v["shape"] == "rewardkit"]
HEREDOC = [k for k, v in TASKS.items() if v["shape"] == "heredoc"]


def task_toml(rel_dir: str) -> str:
    return f"{rel_dir}/task.toml"
