"""OpenClaw subclass adding OpenRouter as a supported provider.

Harbor's bundled OpenClaw adapter restricts the model-provider prefix to
{anthropic, nvidia, openai}. This subclass extends that to include
openrouter and injects the canonical OpenRouter base URL into the
generated openclaw config when no OPENROUTER_BASE_URL override is set.

Usage:

    harbor run --path tasks/... \
        --agent-import-path lib.openclaw_openrouter.OpenClawOpenRouter \
        --model openrouter/anthropic/claude-sonnet-4-5

Requires OPENROUTER_API_KEY in env (forwarded by OpenClaw's
_provider_env_keys convention: <PROVIDER>_API_KEY + <PROVIDER>_BASE_URL).
"""

from harbor.agents.installed.openclaw import OpenClaw


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
