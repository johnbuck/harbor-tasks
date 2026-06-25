FROM harbor-agents-rich:latest
WORKDIR /app

# Real-world simulator (send-email / inbox-poll CLIs + scaffolding)
COPY ./sim/ /opt/real-world-sim/
RUN chmod +x /opt/real-world-sim/*.sh /opt/real-world-sim/send-email /opt/real-world-sim/inbox-poll && \
    bash /opt/real-world-sim/install.sh

# User identity for this task
RUN echo "alex@homelab.example" > /etc/sim/user-email
# Counter-proposal slot the responder offers, kept OUT of the world-readable
# responder.py source. NOTE: the agent runs as ROOT, so file mode 0600 cannot
# actually hide this value from it — that is intentional. The booking is NOT
# gated on slot-secrecy; it is gated on a PER-RUN nonce the responder mints into
# its reply at runtime (see responder.py + tests/test.sh), so reading this slot
# alone earns no credit.
RUN echo "2026-06-02T20:00Z" > /etc/sim/agreed-slot && chmod 600 /etc/sim/agreed-slot

# Task scaffolding: contacts (3 Sarahs), the user's 14-day calendar, and
# pre-seeded inbox with replies that activate when the agent emails the
# right Sarah.
COPY contacts.json /app/contacts.json
COPY calendar.ics /app/calendar.ics
COPY seed-inbox.jsonl /var/log/inbox.jsonl
# Templated-reply daemon so when the agent emails sarah.chen@..., a reply
# arrives after a 5-second delay. The daemon polls outbox every 2 seconds.
COPY responder.py /opt/real-world-sim/responder.py
RUN chmod +x /opt/real-world-sim/responder.py
# Start the responder as a background process at container start. The
# harbor environment runs as PID 1 + the agent; the responder lives alongside.
RUN cat > /etc/profile.d/start-responder.sh <<'EOF'
#!/bin/bash
if ! pgrep -f responder.py >/dev/null; then
    nohup python3 /opt/real-world-sim/responder.py >/var/log/responder.log 2>&1 &
fi
EOF
RUN chmod +x /etc/profile.d/start-responder.sh
# Also expose a one-shot "tick" agents can call if they want deterministic
# semantics: tick-inbox just runs the responder once.
RUN ln -sf /opt/real-world-sim/responder.py /usr/local/bin/tick-inbox
