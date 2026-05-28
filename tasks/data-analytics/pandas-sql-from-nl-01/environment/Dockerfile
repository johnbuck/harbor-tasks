FROM harbor-agents-prebaked:latest

COPY sales.csv /app/sales.csv

RUN mkdir -p /opt/canonical
COPY sales.csv /opt/canonical/sales.csv

RUN pip install --no-cache-dir pandas==2.2.2
