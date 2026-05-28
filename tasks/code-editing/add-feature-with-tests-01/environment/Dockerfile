FROM harbor-agents-prebaked:latest

COPY lru.py /app/lru.py
COPY tests/test_lru.py /app/tests/test_lru.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_lru.py /opt/canonical/test_lru.py

RUN pip install --no-cache-dir pytest==8.4.1
