FROM harbor-agents-rich:latest
WORKDIR /app

# sub-agent fan-out task. 60 PROSE word-problems, HETEROGENEOUS by construction
# (variable op count/order; add/sub/multiply + 1-2 value-dependent branches whose
# outcome is stated as a RULE, never pre-resolved; distractor numbers; digit vs
# spelled-out mix). A generic regex/one-liner cannot reproduce the answers -- the
# branch outcome requires computing the running total -- so the batch is not
# script-one-shottable (the prior fixed-template version was: a ~20-line regex
# reproduced 60/60). Answer per file is a single deterministic integer.
#
# Delegation is the discriminator: enough problems that a serial token-stream
# risks not finishing under the agent budget, while fanning out to sub-agents
# (openclaw sessions_spawn / hermes delegate_task) clears more -> higher
# correct/60 base. No concurrency bonus; delegation = serial-timeout -> lower base.
#
# Leak-proof: only the PROSE lands in the agent container (/app/problems). The
# answer key lives solely in tests/answers.json (verifier) and solution/ (oracle)
# -- neither is mounted into the agent's container during a real run. The
# generator (solution/gen.py) is verifier-side and is NOT in this build context.
RUN mkdir -p /app/problems /app/out /var/log \
    && touch /var/log/work.log && chmod 666 /var/log/work.log

# Static, pre-generated prose problems (authored via gen_subagent_problems.py).
COPY problems/ /app/problems/
