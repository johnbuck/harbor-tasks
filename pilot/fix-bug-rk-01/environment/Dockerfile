FROM harbor-agents-prebaked:latest

COPY wordcount.py /app/wordcount.py
COPY tests/test_wordcount.py /app/tests/test_wordcount.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_wordcount.py /opt/canonical/test_wordcount.py

RUN pip install --no-cache-dir pytest==8.4.1

# rewardkit runs via uvx at verify time; provide uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
