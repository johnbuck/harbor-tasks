FROM harbor-agents-rich:latest
WORKDIR /app

# Static corpus served on localhost:8780. The agent navigates via curl/wget.
COPY corpus /opt/corpus

# Launch script: starts a python http.server in the background bound to
# 127.0.0.1:8780, then exec's whatever the harness wants. Idempotent.
RUN cat > /usr/local/bin/start-corpus <<'EOF'
#!/bin/bash
if ! pgrep -f "http.server.*8780" >/dev/null; then
    cd /opt/corpus
    nohup python3 -m http.server 8780 --bind 127.0.0.1 >/var/log/corpus.log 2>&1 &
    sleep 0.5
fi
EOF
RUN chmod +x /usr/local/bin/start-corpus

# Auto-start the corpus on shell entry so agents see it.
RUN echo "start-corpus" > /etc/profile.d/start-corpus.sh && chmod +x /etc/profile.d/start-corpus.sh

# The agent might invoke /bin/sh or python without going through profile; start
# the server during image build via an ENTRYPOINT-adjacent script. Harbor runs
# the agent as a non-login shell. Safest: provide a "fetch" helper that
# auto-starts the server before each curl.
RUN cat > /usr/local/bin/fetch <<'EOF'
#!/bin/bash
# fetch <path>  →  GETs http://localhost:8780/<path>; auto-starts the server.
start-corpus
exec curl -fsS "http://127.0.0.1:8780/$1"
EOF
RUN chmod +x /usr/local/bin/fetch
