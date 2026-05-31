FROM harbor-agents-rich:latest

COPY settings.py /app/settings.py
COPY tests/test_settings.py /app/tests/test_settings.py
RUN touch /app/tests/__init__.py

# Pristine copy of the test, used by the verifier to detect tampering.
RUN mkdir -p /opt/canonical
COPY tests/test_settings.py /opt/canonical/test_settings.py

# Install Pydantic v2 (deliberately without pydantic-settings — agent must add it).
RUN pip install --no-cache-dir "pydantic==2.9.0" pytest==8.4.1
