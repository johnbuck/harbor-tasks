FROM harbor-agents-rich:latest

COPY stringutils.py /app/stringutils.py
RUN mkdir -p /app/tests && touch /app/tests/__init__.py

# Pristine impl (tamper check) + planted mutant (used by the verifier only).
RUN mkdir -p /opt/canonical
COPY stringutils.py /opt/canonical/stringutils.py
COPY mutant_stringutils.py /opt/canonical/mutant_stringutils.py

RUN pip install --no-cache-dir pytest==8.4.1 "anthropic>=0.40.0"
