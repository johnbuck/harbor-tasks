FROM harbor-agents-rich:latest

COPY geometry/ /app/geometry/
COPY main.py /app/main.py
COPY tests/test_geometry.py /app/tests/test_geometry.py
RUN touch /app/tests/__init__.py

# Pristine copy of the test, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical
COPY tests/test_geometry.py /opt/canonical/test_geometry.py

# Hidden contract grader (NOT under /app — the agent can't see or game it).
# The verifier runs it to score the package-export / empty / raise / no-dead-code
# rules the visible tests don't enforce.
COPY hidden_grader.py /opt/canonical/hidden_grader.py

RUN pip install --no-cache-dir pytest==8.4.1
