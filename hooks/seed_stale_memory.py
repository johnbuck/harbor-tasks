"""TrialEvent.START hook: seed a STALE memory into the per-agent hindsight bank,
scoped to the T3 trial (multistep-stale-memory-vs-file-01) only.

WHY: T3 is a stale-memory-vs-ground-truth-file discriminator. Step 01 has the
agent read `cache_ttl_seconds: 45` from /app/config.yaml; step 04 flips the file
on disk to 275 and asks for the value again. The harness signal is whether the
agent answers from a STALE memory (45) or re-reads the now-authoritative file
(275). For that contrast to MEASURE the harness rather than luck, BOTH harnesses
must start step 04 with the same stale belief in memory. We plant it mechanically
here so the trap does not depend on the agent having chosen to memorise it in an
earlier step.

This mirrors hooks/wipe_memory_state.py IN REVERSE: the wipe empties the eval-*
banks before every trial; this hook then WRITES one memory back, but ONLY for the
T3 trial. It MUST run AFTER the wipe hook (registration order in the driver
guarantees this) or the wipe would delete the seed.

SCOPE / SAFETY:
  * Fires only when event.task_name names the T3 task (TASK_MATCH substring), so
    it never poisons unrelated trials.
  * Reuses GROUP_MAP + _assert_eval_scope from the wipe hook, so it can only ever
    touch an eval-<harness> bank — never a production bank (juliet/yui/akane).
  * Hindsight unreachable / non-2xx => log a warning and continue; like the wipe
    hook it must not block the trial on an infra flake.

WIRE-UP in the sweep driver (AFTER the wipe hook):

    from hooks.seed_stale_memory import seed_stale_memory
    job.add_hook(TrialEvent.START, seed_stale_memory)

OPEN (D7 / run-dependent): the exact hindsight "create memory" request schema is
confirmed against the live API as part of the symmetry check (acceptance 1b). The
body below posts the stale fact as natural-language content plus a metadata value;
if the live build names the field differently, adjust here — the wipe hook only
exercised the DELETE side so the create shape could not be derived offline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import httpx

from hooks.wipe_memory_state import (
    HINDSIGHT_BASE,
    _assert_eval_scope,
    _resolve_group,
)

if TYPE_CHECKING:
    from harbor.trial.hooks import TrialHookEvent

logger = logging.getLogger(__name__)

# Only this trial gets a seeded memory. Matches both the task.toml name
# ("johnbuck/multistep-stale-memory-vs-file-01") and the directory basename
# Harbor may report, since the slug is a substring of both.
TASK_MATCH = "multistep-stale-memory-vs-file-01"

# The stale value the agent first saw in step 01 (config.yaml is flipped to 275
# in step 04's setup.sh; the stale belief must be the pre-flip value).
STALE_TTL_SECONDS = 45


def _seed_hindsight(bank_id: str) -> None:
    """Write the single stale-TTL memory into the eval bank's /memories.

    The bank shell + entity-type config are left intact (the wipe hook preserves
    them); we only add one memory-bearing row.
    """
    _assert_eval_scope(bank_id)  # never write into a real agent's bank
    base = f"{HINDSIGHT_BASE}/v1/default/banks/{bank_id}"
    content = (
        f"The cache_ttl_seconds setting in /app/config.yaml is "
        f"{STALE_TTL_SECONDS} seconds."
    )
    body = {
        "content": content,
        "metadata": {
            "source": "eval-seed",
            "key": "cache_ttl_seconds",
            "value": STALE_TTL_SECONDS,
        },
    }
    with httpx.Client(timeout=15.0) as client:
        r = client.post(f"{base}/memories", json=body)
        if r.status_code not in (200, 201, 202):
            logger.warning("hindsight seed %s/memories -> %s: %s",
                           base, r.status_code, r.text[:200])


async def seed_stale_memory(event: "TrialHookEvent") -> None:
    """TrialEvent.START callback. For the T3 trial ONLY, seed the stale
    cache_ttl_seconds=45 memory into the trial's eval-<harness> hindsight bank.

    Must be registered AFTER wipe_memory_state so the wipe does not delete the
    seed. No-ops (logs + returns) for any other task or unmapped agent.
    """
    task_name = event.task_name or ""
    if TASK_MATCH not in task_name:
        logger.debug("seed_stale_memory: skipping non-T3 task %r", task_name)
        return

    agent = event.config.agent
    agent_name = agent.name if agent and agent.name else None
    if not agent_name and agent and agent.import_path:
        agent_name = agent.import_path.rsplit(":", 1)[-1]
    group_id = _resolve_group(agent_name)
    if group_id is None:
        logger.debug("seed_stale_memory: no group mapping for agent %r", agent_name)
        return

    logger.info("seeding stale memory for trial=%s group=%s (cache_ttl_seconds=%d)",
                event.trial_id, group_id, STALE_TTL_SECONDS)

    # Run off the event loop; a hindsight flake (or the eval-scope guard tripping)
    # must log and continue rather than block the trial.
    result = await asyncio.gather(
        asyncio.to_thread(_seed_hindsight, group_id),
        return_exceptions=True,
    )
    if isinstance(result[0], Exception):
        logger.warning("seed_stale_memory: hindsight seed failed for group=%s: %s",
                       group_id, result[0])
