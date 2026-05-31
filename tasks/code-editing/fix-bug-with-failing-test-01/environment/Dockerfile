FROM harbor-agents-rich:latest

# Buggy code the agent will fix:
COPY wordcount.py /app/wordcount.py

# Test file the agent will run against:
COPY tests/test_wordcount.py /app/tests/test_wordcount.py
RUN touch /app/tests/__init__.py

# Pristine copy of the test, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical
COPY tests/test_wordcount.py /opt/canonical/test_wordcount.py

# Pytest for the verifier (and for the agent if it wants to run it).
RUN pip install --no-cache-dir pytest==8.4.1
