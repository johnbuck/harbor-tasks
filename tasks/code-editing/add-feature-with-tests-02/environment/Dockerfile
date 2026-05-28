FROM harbor-agents-prebaked:latest

COPY calc.py /app/calc.py
COPY tests/test_calc.py /app/tests/test_calc.py
RUN touch /app/tests/__init__.py

RUN mkdir -p /opt/canonical
COPY tests/test_calc.py /opt/canonical/test_calc.py

RUN pip install --no-cache-dir pytest==8.4.1
