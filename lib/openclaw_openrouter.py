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
        "cache_write": 3.75,
    },
    "openrouter/anthropic/claude-opus-4-5": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "anthropic/claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
}


def _compute_cost_usd(
    model_name: str,
    real_input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int = 0,
) -> float | None:
    """Return total cost in USD, or None if the model isn't priced.

    Takes raw token counts as the agent reports them — NOT Harbor's
    combined n_input_tokens convention. Callers must split the
    real_input from cache_read themselves.
    """
    prices = _PRICES_PER_MTOK.get(model_name)
    if not prices:
        return None
    return (
        real_input_tokens * prices["input"] / 1_000_000
        + output_tokens * prices["output"] / 1_000_000
        + cache_read_tokens * prices["cache_read"] / 1_000_000
        + cache_write_tokens * prices["cache_write"] / 1_000_000
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
        # Fall-back cost calc when the subclass (or any other path) doesn't
        # override with the cache_write-aware version. Approximate — assumes
        # cache_write = 0. The NoInstall subclass overrides this with the
        # accurate session-jsonl-based reader.
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
