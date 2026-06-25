FROM harbor-agents-rich:latest

# Judge dependency, pre-installed so the verifier runs fast and offline-of-pip.
RUN pip install --no-cache-dir "anthropic>=0.40.0"

COPY setup.md /app/setup.md
