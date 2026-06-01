FROM harbor-agents-rich:latest

# Code the agent will work on:
COPY calc.py /app/calc.py

# Test file the agent will run against:
COPY tests/test_calc.py /app/tests/test_calc.py
RUN touch /app/tests/__init__.py

# Pristine copy of the test, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical
COPY tests/test_calc.py /opt/canonical/test_calc.py

# Hidden contract grader (NOT under /app — the agent can't see or game it).
# The verifier runs it to score the contract edge-cases the visible tests
# don't enforce.
COPY hidden_grader.py /opt/canonical/hidden_grader.py

# Pytest for the verifier (and for the agent if it wants to run it).
RUN pip install --no-cache-dir pytest==8.4.1
