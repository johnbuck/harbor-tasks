FROM harbor-agents-rich:latest
WORKDIR /app
# Generate the ~100k-line incident log at build (narration-free; causal lines
# buried in routine traffic). See gen_log.py for the rework rationale.
COPY gen_log.py /tmp/gen_log.py
RUN python3 /tmp/gen_log.py && rm /tmp/gen_log.py
