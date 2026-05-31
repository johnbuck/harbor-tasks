FROM harbor-agents-rich:latest
WORKDIR /app
COPY budget.csv /app/budget.csv
COPY budget.expected.csv /app/.budget.expected.csv
RUN chmod 444 /app/.budget.expected.csv
