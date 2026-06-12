"""TrialEvent.START hook: wipe per-agent memory state on each of the three eval
memory backends (recall / hindsight / honcho) before every trial.

WHY: cross-run memory contamination is the single biggest confound the
literature flags ([2502.01534], Mem0 2026). Without this, harness-A's writes
pollute harness-B's later trials and bias the comparison.

WIRE-UP in the sweep driver:

    from harbor.trial.hooks import TrialEvent
    from hooks.wipe_memory_state import wipe_memory_state
    job.add_hook(TrialEvent.START, wipe_memory_state)

GROUPS: agent name → memory keys
    openclaw → recall group eval-openclaw, hindsight bank eval-openclaw,
               honcho workspace eval-openclaw
    hermes   → recall group eval-hermes, hindsight bank eval-hermes,
               honcho workspace eval-hermes

SECRET HYGIENE: Neo4j password is never read into this process. The recall wipe
SSHes to the memory host and runs cypher-shell with the password read *inside* the
container (`printenv NEO4J_AUTH | cut -d/ -f2`) so it never enters our context.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import subprocess
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from harbor.trial.hooks import TrialHookEvent

logger = logging.getLogger(__name__)

RECALL_CONTAINER = "recall-neo4j"
# Internal endpoints injected at runtime from the gitignored configs/local.env
# (exported into the harbor process env). Kept out of this public repo.
HINDSIGHT_BASE = os.environ.get("HINDSIGHT_URL", "")
HONCHO_BASE = os.environ.get("HONCHO_URL", "")
MEMORY_HOST_SSH = os.environ.get("MEMORY_HOST_SSH", "")

# DATA-SAFETY INVARIANT: this hook deletes memory. It must only ever touch the
# dedicated eval namespaces — NEVER the production agents that share the same
# backends. recall-neo4j holds the production memory groups; honcho and
# hindsight are likewise shared with real agents. Every group/workspace/bank id
# this hook deletes MUST start with this prefix. `_assert_eval_scope` enforces it
# at the destructive call site, so even a future GROUP_MAP typo cannot wipe prod.
EVAL_PREFIX = "eval-"

# agent name (lowercase, as Harbor reports) → eval group key
GROUP_MAP = {
    "openclaw": "eval-openclaw",
    "openclawthin": "eval-openclaw",
    "openclawnoinstall": "eval-openclaw",
    "openclawnoinstallopenrouter": "eval-openclaw",
    "hermes": "eval-hermes",
    "hermesthin": "eval-hermes",
    "hermesnoinstall": "eval-hermes",
}


def _assert_eval_scope(group_id: str) -> None:
    """Refuse to operate on anything outside the eval-* namespace.

    Defense in depth against accidentally wiping production memory (the
    production memory groups in recall, real workspaces in honcho/hindsight). Raises ValueError on
    any non-eval id; the caller logs it and skips the wipe rather than guessing.
    """
    if not isinstance(group_id, str) or not group_id.startswith(EVAL_PREFIX):
        raise ValueError(
            f"refusing to wipe non-eval memory scope {group_id!r} "
            f"(must start with {EVAL_PREFIX!r})"
        )


def _resolve_group(agent_name: str | None) -> str | None:
    if not agent_name:
        return None
    key = agent_name.lower().replace("-", "").replace("_", "")
    return GROUP_MAP.get(key)


def _wipe_recall(group_id: str) -> None:
    """Wipe Graphiti graph rows for the given group_id via cypher.

    Password is read inside the container; never enters our process env.
    """
    _assert_eval_scope(group_id)  # never delete the production memory groups
    cypher = f'MATCH (n {{group_id: "{group_id}"}}) DETACH DELETE n'
    inner = (
        f'PASS=$(printenv NEO4J_AUTH | cut -d/ -f2); '
        f'cypher-shell -u neo4j -p "$PASS" {shlex.quote(cypher)}'
    )
    cmd = [
        "ssh", MEMORY_HOST_SSH,
        f'docker exec {RECALL_CONTAINER} sh -c {shlex.quote(inner)}',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.warning("recall wipe failed for %s: %s", group_id, result.stderr.strip())


def _hindsight_delete_listed(client: "httpx.Client", base: str, resource: str) -> None:
    """List a hindsight sub-resource (GET .../{resource} → {items:[...]}) and
    DELETE each by id. Used for resources with no bulk-delete endpoint
    (mental-models, directives, documents)."""
    offset = 0
    while True:
        r = client.get(f"{base}/{resource}", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            if r.status_code != 404:
                logger.warning("hindsight list %s/%s → %s", base, resource, r.status_code)
            return
        items = r.json().get("items", [])
        if not items:
            return
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            d = client.delete(f"{base}/{resource}/{item_id}")
            if d.status_code not in (200, 202, 204, 404):
                logger.warning("hindsight delete %s/%s/%s → %s",
                               base, resource, item_id, d.status_code)
        if len(items) < 100:
            return
        offset += len(items)


def _wipe_hindsight(bank_id: str) -> None:
    """Empty the hindsight bank's contents, preserving the bank + its config.

    The bank shell (and the eval-domain entity-type config from task #59) is
    KEPT — deleting the bank would strip that config. We clear the memory-bearing
    contents only:
      * bulk DELETE /memories and /observations (these endpoints exist);
      * per-id delete of mental-models / directives / documents (no bulk route).
    Entities have no delete endpoint in this hindsight build; they are derived
    from memories/observations, so clearing those removes their substrate.
    """
    _assert_eval_scope(bank_id)  # never touch a real agent's bank
    base = f"{HINDSIGHT_BASE}/v1/default/banks/{bank_id}"
    with httpx.Client(timeout=15.0) as client:
        for bulk in ("memories", "observations"):
            r = client.delete(f"{base}/{bulk}")
            if r.status_code not in (200, 202, 204, 404):
                logger.warning("hindsight bulk wipe %s/%s → %s", base, bulk, r.status_code)
        for resource in ("mental-models", "directives", "documents"):
            _hindsight_delete_listed(client, base, resource)


def _honcho_delete_all(client: "httpx.Client", list_url: str, del_url_for) -> None:
    """Page through a honcho list endpoint and DELETE every item.

    `del_url_for(item_id)` builds the per-item DELETE URL. honcho's list
    endpoints are POST {} with {items, page, pages}; DELETEs return 200/202/204.
    """
    page = 1
    while True:
        r = client.post(list_url, json={}, params={"page": page})
        if r.status_code != 200:
            logger.warning("honcho list %s → %s", list_url, r.status_code)
            return
        body = r.json()
        for item in body.get("items", []):
            item_id = item.get("id")
            if not item_id:
                continue
            d = client.delete(del_url_for(item_id))
            if d.status_code not in (200, 202, 204, 404):
                logger.warning("honcho delete %s → %s", del_url_for(item_id), d.status_code)
        if page >= body.get("pages", 1):
            return
        page += 1


def _wipe_honcho(workspace_id: str) -> None:
    """Empty the honcho workspace in place: delete all conclusions + sessions.

    We do NOT delete the workspace itself — that 409s while sessions remain, and
    deleting it risks a recreate race if the next trial writes before honcho
    lazily re-creates it. Emptying the two memory-bearing resources (derived
    `conclusions` + message `sessions`) clears cross-trial memory while leaving
    the workspace/peer shell intact. Deleting a session also clears its messages;
    conclusions are deleted explicitly in case they outlive their session.
    """
    _assert_eval_scope(workspace_id)  # never empty a real agent's workspace
    base = f"{HONCHO_BASE}/v3/workspaces/{workspace_id}"
    with httpx.Client(timeout=10.0) as client:
        _honcho_delete_all(
            client,
            f"{base}/conclusions/list",
            lambda cid: f"{base}/conclusions/{cid}",
        )
        _honcho_delete_all(
            client,
            f"{base}/sessions/list",
            lambda sid: f"{base}/sessions/{sid}",
        )


async def wipe_memory_state(event: "TrialHookEvent") -> None:
    """TrialEvent.START callback. Resolves the eval group from the trial's
    agent name and wipes recall + hindsight + honcho state for that group.

    Safe to fire when memory backends are unreachable; logs a warning and
    continues so the trial isn't blocked by infrastructure flakes.
    """
    # YAML agents are defined by import_path (e.g. "lib.openclaw_thin:OpenClawThin")
    # with no explicit `name`, so AgentConfig.name stays None. Fall back to the
    # class name parsed off import_path (…:OpenClawThin → "openclawthin", which is
    # already in GROUP_MAP).
    agent = event.config.agent
    agent_name = agent.name if agent and agent.name else None
    if not agent_name and agent and agent.import_path:
        agent_name = agent.import_path.rsplit(":", 1)[-1]
    group_id = _resolve_group(agent_name)
    if group_id is None:
        logger.debug("wipe_memory_state: no group mapping for agent %r", agent_name)
        return

    logger.info("wiping memory state for trial=%s group=%s", event.trial_id, group_id)

    # Run all three wipes concurrently; each is independent. return_exceptions
    # keeps one backend's flake (or the eval-scope guard tripping) from blocking
    # the trial — but surface any failure so a misconfiguration isn't silent.
    backends = ("recall", "hindsight", "honcho")
    results = await asyncio.gather(
        asyncio.to_thread(_wipe_recall, group_id),
        asyncio.to_thread(_wipe_hindsight, group_id),
        asyncio.to_thread(_wipe_honcho, group_id),
        return_exceptions=True,
    )
    for backend, result in zip(backends, results):
        if isinstance(result, Exception):
            logger.warning("wipe_memory_state: %s wipe failed for group=%s: %s",
                           backend, group_id, result)
