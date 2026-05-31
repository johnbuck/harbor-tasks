#!/bin/bash
# Install the real-world-sim CLIs + scaffolding into a task container.
# Invoked from a task's environment/Dockerfile after COPYing this dir to /opt/.
set -euo pipefail

mkdir -p /etc/sim /var/log

# Install CLIs to /usr/local/bin.
for tool in send-email inbox-poll; do
    install -m 0755 "/opt/real-world-sim/$tool" "/usr/local/bin/$tool"
done

# Default user identity (a task can override by writing /etc/sim/user-email).
if [ ! -f /etc/sim/user-email ]; then
    echo "user@example.com" > /etc/sim/user-email
fi

# Initialize empty mailboxes (task can seed these).
touch /var/log/outbox.jsonl /var/log/inbox.jsonl
chmod 666 /var/log/outbox.jsonl /var/log/inbox.jsonl
