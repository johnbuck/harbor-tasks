FROM harbor-agents-rich:latest

COPY sales.csv /app/sales.csv
COPY products.csv /app/products.csv

RUN mkdir -p /opt/canonical
COPY sales.csv /opt/canonical/sales.csv
COPY products.csv /opt/canonical/products.csv

RUN pip install --no-cache-dir pandas==2.2.2
