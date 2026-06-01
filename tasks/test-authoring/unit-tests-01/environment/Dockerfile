FROM harbor-agents-rich:latest

COPY stringutils.py /app/stringutils.py
RUN mkdir -p /app/tests && touch /app/tests/__init__.py

# Pristine impl (tamper check) + planted mutants (used by the verifier only).
RUN mkdir -p /opt/canonical/mutants
COPY stringutils.py /opt/canonical/stringutils.py
COPY mutants/ /opt/canonical/mutants/

RUN pip install --no-cache-dir pytest==8.4.1
