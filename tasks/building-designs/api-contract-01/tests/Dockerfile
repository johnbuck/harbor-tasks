# Separate-verifier image (environment_mode = "separate"). Harbor builds this from
# tests/ and runs /tests/test.sh inside it with skip_tests_upload=True — the image
# must OWN the grader. rewardkit + pyyaml are BAKED so grading needs no runtime
# network (FOOTGUNS #42).
FROM harbor-agents-rich:latest
RUN pip install --no-cache-dir harbor-rewardkit==0.1.4 "pyyaml==6.0.2"
COPY test.sh reward.py /tests/
RUN chmod +x /tests/test.sh
