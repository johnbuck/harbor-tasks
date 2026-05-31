FROM harbor-agents-rich:latest

COPY intervals.py /app/intervals.py
COPY tests/test_intervals.py /app/tests/test_intervals.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_intervals.py /opt/canonical/test_intervals.py

RUN pip install --no-cache-dir pytest==8.4.1
