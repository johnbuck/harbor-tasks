# Separate-verifier image (environment_mode = "separate").
#
# Harbor builds the verifier sandbox from the tests/ build context and runs
# /tests/test.sh INSIDE it with skip_tests_upload=True — i.e. it does NOT upload
# tests/ at grade time; the image must already OWN the grader. So we bake the
# grader scripts into /tests here. rewardkit is BAKED at build time so grading
# has NO runtime PyPI dependency (the prototype's per-trial `uvx` fetch pulled 56
# packages — a grading-integrity risk if PyPI is slow/down).
FROM harbor-agents-rich:latest
RUN pip install --no-cache-dir harbor-rewardkit==0.1.4
COPY test.sh reward.py /tests/
RUN chmod +x /tests/test.sh
