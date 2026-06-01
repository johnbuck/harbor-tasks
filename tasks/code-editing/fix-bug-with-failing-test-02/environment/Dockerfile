FROM harbor-agents-rich:latest

# Buggy code the agent will fix:
COPY running_total.py /app/running_total.py

# Test file the agent will run against:
COPY tests/test_running_total.py /app/tests/test_running_total.py
RUN touch /app/tests/__init__.py

# Pristine copy of the test, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical
COPY tests/test_running_total.py /opt/canonical/test_running_total.py

# Hidden contract grader (NOT under /app — the agent can't see or game it).
# The verifier runs it to score the no-mutation / None-gap rules that the
# visible tests don't enforce.
COPY hidden_grader.py /opt/canonical/hidden_grader.py

# Pytest for the verifier (and for the agent if it wants to run it).
RUN pip install --no-cache-dir pytest==8.4.1
