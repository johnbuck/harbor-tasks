FROM harbor-agents-prebaked:latest

COPY repo/ /app/repo/

# Pristine copy of the repo, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical/repo
COPY repo/ /opt/canonical/repo/
