FROM harbor-agents-rich:latest
WORKDIR /app

# Static corpus (Halcyon Systems knowledge base) served on localhost:8780. The
# agent navigates via curl/fetch and must distinguish current authoritative pages
# from archived/legacy near-duplicates. Verifier is deterministic (no LLM judge).
COPY corpus /opt/corpus

RUN cat > /usr/local/bin/start-corpus <<'EOF'
#!/bin/bash
if ! pgrep -f "http.server.*8780" >/dev/null; then
    cd /opt/corpus
    nohup python3 -m http.server 8780 --bind 127.0.0.1 >/var/log/corpus.log 2>&1 &
    sleep 0.5
fi
EOF
RUN chmod +x /usr/local/bin/start-corpus

RUN echo "start-corpus" > /etc/profile.d/start-corpus.sh && chmod +x /etc/profile.d/start-corpus.sh

RUN cat > /usr/local/bin/fetch <<'EOF'
#!/bin/bash
# fetch <path>  →  GETs http://localhost:8780/<path>; auto-starts the server.
start-corpus
exec curl -fsS "http://127.0.0.1:8780/$1"
EOF
RUN chmod +x /usr/local/bin/fetch
