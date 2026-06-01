FROM harbor-agents-rich:latest
WORKDIR /app
# Seed the config the agent will read + memorize. Its cache_ttl_seconds starts
# at 45; step 04's setup.sh silently rewrites it to 275 BEFORE the final
# question, so the on-disk ground truth diverges from what the agent stored in
# memory across the earlier turns.
RUN cat > /app/config.yaml <<'YAML'
service: edge-cache
region: us-west-2
cache_ttl_seconds: 45
max_connections: 200
log_level: info
YAML
