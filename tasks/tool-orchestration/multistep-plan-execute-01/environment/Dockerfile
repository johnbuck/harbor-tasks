FROM harbor-agents-rich:latest
WORKDIR /app
RUN pip install --no-cache-dir pytest==8.4.1

# Seed a sample CSV the agent can use while developing csv2json.py.
RUN printf '%s\n' \
    'name,age,city' \
    'Alice,30,London' \
    'Bob,25,Paris' \
    'Cleo,42,Paris' \
    'Dan,19,Berlin' > /app/people.csv
