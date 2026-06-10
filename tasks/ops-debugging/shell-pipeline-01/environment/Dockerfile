FROM harbor-agents-rich:latest

COPY access.log /app/access.log

# Pristine copy for tamper detection.
RUN mkdir -p /opt/canonical
COPY access.log /opt/canonical/access.log

# rewardkit for the shared-mode grader (tests/reward.py). Self-contained in this
# task's image — no shared base change.
RUN pip install --no-cache-dir harbor-rewardkit==0.1.4
