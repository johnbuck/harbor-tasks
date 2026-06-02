FROM harbor-agents-rich:latest
WORKDIR /app

# REDESIGN 2026-06-01 (sub-agent fan-out, for real this time).
#
# The old version was 32 CSVs needing the same DETERMINISTIC filter+sort+summary
# transform -> a single shell/python script one-shots all 32 in <1s, so fan-out
# was never REQUIRED and the parallelism "bonus" was mathematically inert (it
# clamped to 1.0 for serial AND parallel when base=1.0).
#
# New design: 60 PROSE word-problems. Each needs genuine multi-step reasoning
# (read a scenario, track a value through 5 sequential operations including a
# value-dependent branch) -> NOT solvable by a generic script, and the answer is
# a single deterministic integer. There are enough of them that solving all 60
# SERIALLY in one token-stream blows the wall-clock budget, while fanning out to
# sub-agents (openclaw sessions_spawn / hermes delegate_task) finishes far more
# of them in time. So the FRACTION solved (a non-clamped base reward) itself
# separates a harness that fans out from one that grinds serially -- no inert
# bonus needed.
#
# Leak-proof: only the PROSE lands in the agent container (/app/problems). The
# answer key lives solely in tests/answers.json (verifier) and solution/
# answers.json (oracle) -- neither is mounted into the agent's container during a
# real run. The generator itself is NOT shipped in the image.
RUN mkdir -p /app/problems /app/out /var/log \
    && touch /var/log/work.log && chmod 666 /var/log/work.log

# Static, pre-generated prose problems (authored via gen_subagent_problems.py).
COPY problems/ /app/problems/
