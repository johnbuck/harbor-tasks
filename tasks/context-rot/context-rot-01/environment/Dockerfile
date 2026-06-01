FROM harbor-agents-rich:latest
WORKDIR /app
COPY gen_reports.py /tmp/gen_reports.py
RUN python3 /tmp/gen_reports.py && rm /tmp/gen_reports.py
