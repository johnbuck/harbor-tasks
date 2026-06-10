# harbor-agents-rich
# ---
# Extends harbor-agents-prebaked with the harnesses' OWN rich configs baked in:
# reasoning ON, persona, memory MCP servers, skills enabled. The thin Harbor
# adapters (lib/openclaw_thin.py, lib/hermes_thin.py) only INVOKE the baked
# harness and capture metrics — they do NOT regenerate config. This is the
# "STOP USING THE PACKAGED HARNESSES" direction (FOOTGUNS #12).
#
# Build (context MUST be the repo root so COPY can read harnesses/):
#   environments/agent-rich/build.sh
# build.sh sources the gitignored configs/local.env and passes the internal
# memory-service endpoints as build-args — this PUBLIC repo holds only
# __HINDSIGHT_URL__ / __HONCHO_URL__ placeholders in the baked configs.
#
# Verify:
#   docker run --rm harbor-agents-rich:latest bash -lc \
#     '. ~/.nvm/nvm.sh && nvm use 22 >/dev/null && openclaw config validate && hermes version'

FROM harbor-agents-prebaked:latest

# --- Skill-enabling runtime deps (unlock requirement-gated skills) -----------
# python-debugpy (debugging) + data-science/jupyter skills gate on these bins
# being importable by the task python3. Installed into the base interpreter the
# agents' code_execution uses.
RUN pip install --no-cache-dir debugpy==1.8.* ipykernel==6.* jupyterlab==4.* \
    && python3 -m ipykernel install --name python3 --display-name "Python 3" 2>/dev/null || true

# --- openclaw: bake the rich config + persona --------------------------------
# Config → ~/.openclaw/openclaw.json (custom xrouter provider w/ reasoning:true,
# memory MCP servers, thinkingDefault high, skipBootstrap so no first-run ritual
# pollutes the task dir). Persona workspace files are staged in the image; the
# thin adapter copies them into the per-task working dir at run start (openclaw
# loads SOUL/AGENTS/IDENTITY/USER from the workspace = cwd every session).
RUN mkdir -p /root/.openclaw /opt/harness/openclaw-workspace
COPY harnesses/openclaw/openclaw.json /root/.openclaw/openclaw.json
COPY harnesses/openclaw/workspace/ /opt/harness/openclaw-workspace/

# --- refresh the persisted plugin registry (THE #90 fix) ---------------------
# The base image ships a STALE persisted plugin registry (/root/.openclaw/plugins)
# that was indexed before several stock extensions (notably `browser`, plus
# canvas/file-transfer/phone-control/talk-voice) were fully present, so they were
# never indexed and their tools never surfaced at runtime — embedded OR
# gateway-backed. `registry --refresh` rebuilds it from the current manifests so
# the `browser` tool (and the rest) are available to the agent. Verified: refresh
# takes 46 → 64 enabled plugins and makes `browser` appear in the agent catalog.
# Assert browser is indexed so a future base-image change can't silently drop it.
RUN . ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1 \
    && openclaw plugins registry --refresh >/dev/null 2>&1 \
    && openclaw plugins list --json 2>/dev/null | grep -q '"browser"' \
    && echo "browser plugin indexed OK"

# --- self-contained browser: bake Chromium INTO the image --------------------
# Both harnesses' browser tools attach to a headless Chromium running INSIDE the
# trial container (127.0.0.1:9222), not a shared one on wiley. Debian trixie's
# `chromium` package gives a real /usr/bin/chromium (148, matches the old wiley
# Chrome). /etc/chromium.d/* is sourced by Debian's chromium wrapper, so the
# container flags (--no-sandbox etc., required to run as root) apply to every
# launch. start-cdp.sh brings it up per-trial. Spec:
# backlog/2026-06-03-self-contained-browser.md.
RUN apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        chromium fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /etc/chromium.d \
    && printf '%s\n' 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox --disable-dev-shm-usage --disable-gpu"' \
        > /etc/chromium.d/00-harbor-container \
    && /usr/bin/chromium --version
COPY environments/agent-rich/start-cdp.sh /opt/harness/start-cdp.sh
RUN chmod +x /opt/harness/start-cdp.sh

# --- hermes: bake the rich config over the default template ------------------
# The installer seeds ~/.hermes with a DEFAULT config.yaml (anthropic/opus,
# provider auto, memory off). Overwrite it with our rich config (deepseek via
# OpenRouter, reasoning_effort high, provider_routing deny, memory on,
# mcp_servers recall+hindsight, delegation) and persona SOUL.md.
COPY harnesses/hermes/config.yaml /root/.hermes/config.yaml
COPY harnesses/hermes/SOUL.md /root/.hermes/SOUL.md
# Honcho memory provider: client lib + self-hosted instance config.
# ($HERMES_HOME/honcho.json takes precedence; baseUrl points at wiley, no auth.)
COPY harnesses/hermes/honcho.json /root/.hermes/honcho.json
# hermes uses a uv-managed venv (no pip); install honcho-ai into it via uv.
RUN /root/.local/bin/uv pip install --python /usr/local/lib/hermes-agent/venv/bin/python \
        --no-cache honcho-ai

# --- bake internal endpoints (kept OUT of git; injected at build time) --------
# The committed harness configs carry __HINDSIGHT_URL__ / __HONCHO_URL__ so this
# PUBLIC repo holds no internal topology. Real values arrive as build-args from
# environments/agent-rich/build.sh (which sources gitignored configs/local.env).
# Fail loudly if unset — a bare `docker build` must NOT silently bake broken URLs.
ARG HINDSIGHT_URL
ARG HONCHO_URL
RUN { test -n "$HINDSIGHT_URL" && test -n "$HONCHO_URL"; } \
      || { echo "ERROR: build via environments/agent-rich/build.sh — HINDSIGHT_URL and HONCHO_URL build-args are required" >&2; exit 1; } \
    && sed -i "s|__HINDSIGHT_URL__|$HINDSIGHT_URL|g" /root/.openclaw/openclaw.json /root/.hermes/config.yaml \
    && sed -i "s|__HONCHO_URL__|$HONCHO_URL|g"     /root/.hermes/honcho.json \
    && ! grep -RnE '__(HINDSIGHT|HONCHO)_URL__' /root/.openclaw/openclaw.json /root/.hermes/config.yaml /root/.hermes/honcho.json

# --- fail-fast validation ----------------------------------------------------
# openclaw must parse its config; hermes must still launch with the new config.
RUN . ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1 \
    && openclaw config validate \
    && export PATH="$HOME/.local/bin:/usr/local/bin:$PATH" \
    && HERMES_HOME=/root/.hermes hermes version

WORKDIR /app
