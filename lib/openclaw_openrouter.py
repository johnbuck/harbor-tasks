"""OpenClaw subclass adding OpenRouter as a supported provider + cost computation.

Harbor's bundled OpenClaw adapter:
  * restricts the model-provider prefix to {anthropic, nvidia, openai}, and
  * never sets cost_usd because openclaw's own JSON output doesn't include it.

This subclass:
  1. Extends _SUPPORTED_PROVIDERS to include 'openrouter' and injects the
     canonical OpenRouter base URL when OPENROUTER_BASE_URL isn't set.
  2. Computes cost from tokens × per-model price after the trajectory is
     populated. Uses a small in-class price table; replace with an
     OpenRouter /generation/<id> lookup when ground-truth is needed.

Usage:

    harbor run --path tasks/... \
        --agent-import-path lib.openclaw_openrouter:OpenClawOpenRouter \
        --model openrouter/anthropic/claude-sonnet-4-5

Requires OPENROUTER_API_KEY in env.
"""

from harbor.agents.installed.openclaw import OpenClaw
from harbor.models.agent.context import AgentContext


# Per-million-token prices, USD. Add models as we run them.
# Sources: Anthropic / OpenAI published pricing as of 2026-05-27.
# OpenRouter adds a small markup (~5%); these are list prices.
_PRICES_PER_MTOK = {
    "openrouter/anthropic/claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
    },
    "openrouter/anthropic/claude-opus-4-5": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
    },
    "anthropic/claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
    },
}


def _compute_cost_usd(
    model_name: str,
    n_input_tokens: int,
    n_output_tokens: int,
    n_cache_tokens: int,
) -> float | None:
    """Return total cost in USD, or None if the model isn't priced.

    Harbor's openclaw adapter sets `n_input_tokens = real_input + cache_read`
    and `n_cache_tokens = cache_read` separately. To bill correctly we charge
    cache_read at the discounted cache-read rate and the remainder at the
    full input rate.
    """
    prices = _PRICES_PER_MTOK.get(model_name)
    if not prices:
        return None
    non_cached_input = max(0, n_input_tokens - n_cache_tokens)
    return (
        non_cached_input * prices["input"] / 1_000_000
        + n_output_tokens * prices["output"] / 1_000_000
        + n_cache_tokens * prices["cache_read"] / 1_000_000
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

    def populate_context_post_run(self, context: AgentContext) -> None:
        super().populate_context_post_run(context)
        if context.cost_usd is None and self.model_name:
            context.cost_usd = _compute_cost_usd(
                self.model_name,
                context.n_input_tokens or 0,
                context.n_output_tokens or 0,
                context.n_cache_tokens or 0,
            )
