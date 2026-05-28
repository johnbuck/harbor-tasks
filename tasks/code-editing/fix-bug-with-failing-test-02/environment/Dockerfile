FROM harbor-agents-prebaked:latest

COPY running_total.py /app/running_total.py
COPY tests/test_running_total.py /app/tests/test_running_total.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_running_total.py /opt/canonical/test_running_total.py

RUN pip install --no-cache-dir pytest==8.4.1
