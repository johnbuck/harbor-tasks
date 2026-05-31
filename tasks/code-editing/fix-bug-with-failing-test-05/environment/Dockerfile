FROM harbor-agents-rich:latest

COPY flatten.py /app/flatten.py
COPY tests/test_flatten.py /app/tests/test_flatten.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_flatten.py /opt/canonical/test_flatten.py

RUN pip install --no-cache-dir pytest==8.4.1
