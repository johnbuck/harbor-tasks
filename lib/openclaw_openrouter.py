"""OpenClaw subclass: OpenRouter provider + accurate cost computation.

Harbor's bundled OpenClaw adapter has two gaps for our use case:

  1. Restricts the model-provider prefix to {anthropic, nvidia, openai}.
  2. Never sets cost_usd — openclaw's own JSON doesn't include it.
  3. Its FinalMetrics has no cache_write field, so even if cost computation
     happens downstream it'd miss the 25%-premium cache-write tokens.

This module fixes #1 (subclass below) and #2 (cost helper). The
cache_write fix lives in lib/openclaw_no_install.py where we override
populate_context_post_run to read the openclaw session.jsonl directly
(parallel to HermesNoInstall reading hermes-session.jsonl).

Usage:

    harbor run --path tasks/... \
        --agent-import-path lib.openclaw_openrouter:OpenClawOpenRouter \
        --model openrouter/anthropic/claude-sonnet-4-5

Requires OPENROUTER_API_KEY in env.
"""

import functools
import json
import urllib.request

from harbor.agents.installed.openclaw import OpenClaw
from harbor.models.agent.context import AgentContext


_OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Privacy-floored OpenRouter pool. We route only to upstream hosts that do NOT
# store or train on prompts (`data_collection: "deny"`) and allow fallback
# across all such hosts. This spreads load so a single low-rate-limit host
# (we used to pin "Io Net") can't 429 the whole sweep, while still honoring the
# privacy guardrail: no host retains data for training/storage.
#
# Trade-off vs a single pin: per-host KV caching and per-token price are no
# longer deterministic (OpenRouter load-balances across compliant hosts). The
# comparison stays fair because BOTH harnesses use the same pool, and cost is
# computed from live per-token pricing per call regardless of host.
# Keep in sync with lib/hermes_no_install.py.
OPENROUTER_PROVIDER_ROUTING: dict = {
    "data_collection": "deny",
    "allow_fallbacks": True,
}

# Offline fallback, per-MILLION-token USD. Only consulted when the live
# OpenRouter pricing fetch fails (no network, API down). Live pricing is
# authoritative — do not hand-tune these for accuracy, they're a safety net.
_FALLBACK_PRICES_PER_MTOK = {
    "anthropic/claude-sonnet-4-5": {
        "input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75,
    },
    "deepseek/deepseek-v4-pro": {
        "input": 0.435, "output": 0.870, "cache_read": 0.003625, "cache_write": 0.0,
    },
}


@functools.lru_cache(maxsize=1)
def _openrouter_pricing() -> dict[str, dict[str, float]]:
    """Per-TOKEN USD pricing for every OpenRouter model. Fetched once per process.

    Returns {model_id: {input, output, cache_read, cache_write}} with rates
    already in USD-per-token (OpenRouter's native unit). Empty dict on failure.
    """
    try:
        req = urllib.request.Request(
            _OPENROUTER_MODELS_URL, headers={"User-Agent": "harbor-tasks/eval"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception:
        return {}
    out: dict[str, dict[str, float]] = {}
    for m in data.get("data", []):
        p = m.get("pricing", {})
        try:
            out[m["id"]] = {
                "input": float(p.get("prompt") or 0),
                "output": float(p.get("completion") or 0),
                "cache_read": float(p.get("input_cache_read") or 0),
                "cache_write": float(p.get("input_cache_write") or 0),
            }
        except (TypeError, ValueError, KeyError):
            continue
    return out


def _openrouter_slug(model_name: str) -> str:
    """Strip our 'openrouter/' routing prefix to get the OpenRouter model id."""
    prefix = "openrouter/"
    return model_name[len(prefix):] if model_name.startswith(prefix) else model_name


def _compute_cost_usd(
    model_name: str,
    real_input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int = 0,
) -> float | None:
    """Return total cost in USD, or None if the model can't be priced.

    Live OpenRouter pricing is authoritative (per-token rates). Falls back to
    the hardcoded per-MTok table only if the fetch failed.

    Takes raw token counts as the agent reports them — NOT Harbor's combined
    n_input_tokens convention. Callers split real_input from cache_read.
    """
    slug = _openrouter_slug(model_name)

    live = _openrouter_pricing().get(slug)
    if live:
        return (
            real_input_tokens * live["input"]
            + output_tokens * live["output"]
            + cache_read_tokens * live["cache_read"]
            + cache_write_tokens * live["cache_write"]
        )

    fb = _FALLBACK_PRICES_PER_MTOK.get(slug) or _FALLBACK_PRICES_PER_MTOK.get(model_name)
    if not fb:
        return None
    return (
        real_input_tokens * fb["input"] / 1_000_000
        + output_tokens * fb["output"] / 1_000_000
        + cache_read_tokens * fb["cache_read"] / 1_000_000
        + cache_write_tokens * fb["cache_write"] / 1_000_000
    )


class OpenClawOpenRouter(OpenClaw):
    _SUPPORTED_PROVIDERS = OpenClaw._SUPPORTED_PROVIDERS | {"openrouter"}

    _OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def _merge_provider_base_url_from_env(self, cfg):
        super()._merge_provider_base_url_from_env(cfg)
        if self._model_provider() != "openrouter":
            return
        providers = cfg.setdefault("models", {}).setdefault("providers", {})
        prov = providers.setdefault("openrouter", {})
        if isinstance(prov, dict) and "baseUrl" not in prov:
            prov["baseUrl"] = self._OPENROUTER_BASE_URL
        # Apply the privacy-floored provider pool via OpenRouter's `provider`
        # routing field, passed through openclaw's documented extra-body
        # passthrough.
        if isinstance(prov, dict):
            params = prov.setdefault("params", {})
            params["provider"] = dict(OPENROUTER_PROVIDER_ROUTING)

    def populate_context_post_run(self, context: AgentContext) -> None:
        super().populate_context_post_run(context)
        # Accurate cost from openclaw.session.jsonl (cache_write-aware). Works
        # for both the install-capable path (this class, used for external
        # benchmark task images) and the NoInstall subclass (prebaked image).
        self._populate_from_session_jsonl(context)
        # Fall-back if the session file was absent (e.g. run aborted before any
        # turn completed): approximate from context totals, cache_write=0.
        if context.cost_usd is None and self.model_name:
            real_input = max(
                0, (context.n_input_tokens or 0) - (context.n_cache_tokens or 0)
            )
            context.cost_usd = _compute_cost_usd(
                self.model_name,
                real_input_tokens=real_input,
                output_tokens=context.n_output_tokens or 0,
                cache_read_tokens=context.n_cache_tokens or 0,
                cache_write_tokens=0,
            )

    def _populate_from_session_jsonl(self, context: AgentContext) -> None:
        """Recompute cost from openclaw.session.jsonl with cache_write."""
        session_path = self.logs_dir / "openclaw.session.jsonl"
        if not session_path.exists():
            return
        totals = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}
        try:
            for line in session_path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = row.get("message")
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                for k in totals:
                    totals[k] += int(usage.get(k) or 0)
        except OSError:
            return
        if not any(totals.values()):
            return
        context.n_input_tokens = totals["input"] + totals["cacheRead"]
        context.n_cache_tokens = totals["cacheRead"]
        context.n_output_tokens = totals["output"]
        if self.model_name:
            context.cost_usd = _compute_cost_usd(
                self.model_name,
                real_input_tokens=totals["input"],
                output_tokens=totals["output"],
                cache_read_tokens=totals["cacheRead"],
                cache_write_tokens=totals["cacheWrite"],
            )
