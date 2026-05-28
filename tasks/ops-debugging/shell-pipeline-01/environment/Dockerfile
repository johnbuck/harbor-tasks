FROM harbor-agents-prebaked:latest

COPY access.log /app/access.log

# Pristine copy for tamper detection.
RUN mkdir -p /opt/canonical
COPY access.log /opt/canonical/access.log
