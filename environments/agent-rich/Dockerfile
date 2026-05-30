# harbor-agents-rich
# ---
# Extends harbor-agents-prebaked with the harnesses' OWN rich configs baked in:
# reasoning ON, persona, memory MCP servers, skills enabled. The thin Harbor
# adapters (lib/openclaw_thin.py, lib/hermes_thin.py) only INVOKE the baked
# harness and capture metrics — they do NOT regenerate config. This is the
# "STOP USING THE PACKAGED HARNESSES" direction (FOOTGUNS #12).
#
# Build (context MUST be the repo root so COPY can read harnesses/):
#   docker build -f environments/agent-rich/Dockerfile -t harbor-agents-rich:latest .
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

# --- fail-fast validation ----------------------------------------------------
# openclaw must parse its config; hermes must still launch with the new config.
RUN . ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1 \
    && openclaw config validate \
    && export PATH="$HOME/.local/bin:/usr/local/bin:$PATH" \
    && HERMES_HOME=/root/.hermes hermes version

WORKDIR /app
