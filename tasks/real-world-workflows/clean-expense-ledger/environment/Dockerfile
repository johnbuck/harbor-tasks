FROM harbor-agents-rich:latest
WORKDIR /app
# Ship ONLY the input ledger. The expected result is NEVER materialized in the
# container — the verifier (tests/grade.py) computes it from the rules at grade
# time. (The deprecated version leaked the answer at /app/.budget.expected.csv.)
COPY budget.csv /app/budget.csv
