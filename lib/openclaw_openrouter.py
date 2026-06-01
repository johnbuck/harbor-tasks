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

from harbor.agents.installed.base import CliFlag
from harbor.agents.installed.openclaw import OpenClaw
from harbor.models.agent.context import AgentContext


_OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Reasoning enablement (per openclaw docs https://docs.openclaw.ai/tools/thinking).
#
# openclaw gates `--thinking <level>` on each model's resolved reasoning profile.
# CRITICAL: openclaw's BUILT-IN providers (`openrouter`, `openai`, `anthropic`)
# resolve that profile from their OWN model catalog, NOT from the entry's
# `compat`. A model the catalog doesn't recognize (e.g. `deepseek/deepseek-v4-pro`)
# resolves to "off only", so `--thinking xhigh` is rejected with "Use one of: off".
# Empirically verified 2026-05-28 on BOTH the `openrouter` and `openai` built-in
# providers — same error, so switching built-in providers cannot fix it.
#
# The documented override `models.providers.<p>.models[].compat.supportedReasoningEfforts`
# is honored ONLY for CUSTOM (non-built-in) OpenAI-compatible providers. So we
# register OpenRouter under a CUSTOM provider name (`xrouter`) pointed at its
# OpenAI-compatible endpoint, declare the supported efforts on each model entry,
# and run `--thinking xhigh`. Reasoning is then genuinely ON (never "off").
_PROVIDER = "xrouter"
OPENROUTER_SUPPORTED_REASONING_EFFORTS = ["low", "medium", "high", "xhigh"]

# Thinking level openclaw runs at. Must be one of the declared efforts above.
# Use "high", NOT "xhigh": openclaw's `xhigh` emits a reasoning_effort value that
# deepseek-v4-pro's OpenRouter route rejects (400 "reasoning_effort: Invalid
# option"), whereas `high` is accepted and genuinely reasons. Verified
# in-container 2026-05-28. Keep xhigh in the *declared* list above (it's the gate
# menu) but run at high.
OPENCLAW_THINKING_LEVEL = "high"

# DETERMINISTIC SINGLE-HOST PIN. OpenRouter load-balances each call across many
# upstream hosts for a model; an UNPINNED pool is NOT fair even when both harnesses
# share the pool definition, because they load-balance INDEPENDENTLY — they hit
# different hosts run-to-run, with different per-host KV-cache and per-token price
# (the v9 confound: "openclaw 0 cache hits vs hermes 21,504 on the same model").
# So we pin BOTH harnesses to one host. Any token/cost/cache delta is then the
# HARNESS, not load-balancer luck. A pinned-host outage failing the trial is an
# honest failure. `require_parameters` keeps reasoning_effort from being dropped.
# MUST stay byte-identical to lib/hermes_no_install.py and the two baked configs
# (harnesses/openclaw/openclaw.json, harnesses/hermes/config.yaml).
OPENROUTER_PROVIDER_ROUTING: dict = {
    "data_collection": "deny",
    "only": ["deepseek"],
    "allow_fallbacks": False,
    "require_parameters": True,
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
    """Strip the leading '<provider>/' segment to get the OpenRouter model id.

    e.g. 'xrouter/deepseek/deepseek-v4-pro' -> 'deepseek/deepseek-v4-pro', which
    is both what openclaw sends to the OpenAI endpoint and the OpenRouter
    pricing-table key.
    """
    return model_name.split("/", 1)[1] if "/" in model_name else model_name


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
    # Register OpenRouter under a CUSTOM provider name (NOT the built-in
    # `openrouter`/`openai`), because only custom providers honor the
    # `compat.supportedReasoningEfforts` override that turns thinking on.
    _SUPPORTED_PROVIDERS = OpenClaw._SUPPORTED_PROVIDERS | {_PROVIDER}

    _OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Run at a genuine thinking level (NOT off). openclaw accepts it because we
    # declare the model's supported efforts in _normalize_provider_models_schema.
    CLI_FLAGS = [
        CliFlag(kwarg="thinking", cli="--thinking", type="str",
                default=OPENCLAW_THINKING_LEVEL)
        if f.kwarg == "thinking" else f
        for f in OpenClaw.CLI_FLAGS
    ]

    @classmethod
    def _provider_env_keys(cls, provider: str) -> tuple[str, ...]:
        # The custom `xrouter` provider authenticates with the OpenRouter key.
        # Harbor forwards these env vars into the container; openclaw resolves
        # the provider apiKey/baseUrl from the `<PROVIDER>_*` convention.
        if provider == _PROVIDER:
            return ("XROUTER_API_KEY", "XROUTER_BASE_URL")
        return super()._provider_env_keys(provider)

    def _normalize_provider_models_schema(self, cfg) -> None:
        super()._normalize_provider_models_schema(cfg)
        if self._model_provider() != _PROVIDER:
            return
        prov = (
            (cfg.get("models") or {}).get("providers") or {}
        ).get(_PROVIDER)
        if not isinstance(prov, dict):
            return
        # The catalog-entry id must be the BARE model slug (no provider prefix):
        # openclaw selects "xrouter/deepseek/deepseek-v4-pro", resolves provider
        # `xrouter` + model key `deepseek/deepseek-v4-pro`, then matches the entry
        # by that bare key. Harbor's base fill uses the full prefixed name, which
        # never matches — so the model resolves as unknown ("off only"). Rewrite
        # the entry with the bare slug AND declare reasoning support, so the
        # --thinking gate accepts xhigh and emits the OpenRouter reasoning_effort.
        # `reasoning: true` is REQUIRED: openclaw's thinking resolver returns an
        # off-only profile whenever a catalog row's `reasoning` is false (its
        # default) — BEFORE it ever consults compat. Only with reasoning=true
        # does it read `compat.supportedReasoningEfforts` and expose xhigh.
        # (Verified against openclaw 2026.5.26 dist/thinking-*.js:387/400.)
        slug = _openrouter_slug(self.model_name)
        prov["models"] = [
            {
                "id": slug,
                "name": slug,
                "reasoning": True,
                "compat": {
                    "supportedReasoningEfforts": list(
                        OPENROUTER_SUPPORTED_REASONING_EFFORTS
                    )
                },
            }
        ]

    def _merge_provider_base_url_from_env(self, cfg):
        super()._merge_provider_base_url_from_env(cfg)
        if self._model_provider() != _PROVIDER:
            return
        providers = cfg.setdefault("models", {}).setdefault("providers", {})
        prov = providers.setdefault(_PROVIDER, {})
        if isinstance(prov, dict) and "baseUrl" not in prov:
            prov["baseUrl"] = self._OPENROUTER_BASE_URL
        # A CUSTOM provider does NOT inherit openclaw's built-in env-var auth
        # (that only maps OPENROUTER_API_KEY -> the built-in `openrouter`
        # provider). Point apiKey at an env-template SecretRef so openclaw
        # resolves XROUTER_API_KEY at runtime. This is a MARKER string, not the
        # secret value, so it is safe to write into the config.
        if isinstance(prov, dict):
            prov.setdefault("apiKey", "${XROUTER_API_KEY}")
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
