FROM harbor-agents-rich:latest

COPY stringutils.py /app/stringutils.py
RUN mkdir -p /app/tests && touch /app/tests/__init__.py

# Pristine impl for the verifier's tamper check (identical to /app/stringutils.py,
# so agent-readable is harmless). The grading MUTANTS are NOT baked here — they
# would leak the exact 4 behaviors scored; they live in tests/mutants/ and Harbor
# uploads tests/ to /tests only AFTER the agent runs (invisible during the run).
COPY stringutils.py /opt/canonical/stringutils.py

RUN pip install --no-cache-dir pytest==8.4.1
