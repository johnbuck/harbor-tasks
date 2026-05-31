FROM harbor-agents-rich:latest

COPY geometry/ /app/geometry/
COPY main.py /app/main.py
COPY tests/test_geometry.py /app/tests/test_geometry.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_geometry.py /opt/canonical/test_geometry.py

RUN pip install --no-cache-dir pytest==8.4.1
