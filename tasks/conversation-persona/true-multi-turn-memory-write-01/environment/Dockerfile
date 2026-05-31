FROM harbor-agents-rich:latest
WORKDIR /app

# This task assumes recall (port 8408) + hindsight (8888) MCP servers are
# reachable from inside the trial container. The thin adapters' baked configs
# already point at internal-host for both. The TrialEvent.START hook
# (hooks/wipe_memory_state.py) wipes the eval group/bank before each trial so
# we measure write proactivity, not contamination.

RUN touch /app/.placeholder
