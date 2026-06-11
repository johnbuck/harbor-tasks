# ---------------------------------------------------------------------------
# Stage 1 (throwaway): compile the latency-gated `cal-lookup` from the SERVED
# registry. The CAL-NN -> offset table is embedded as a NON-STRING int array
# (so `strings` on the binary reveals nothing) and the binary is stripped. The
# plaintext environment/registry.json is consumed ONLY in this stage and is
# never copied into the final image, so no agent-readable offset key survives
# in any final-image layer (FOOTGUNS: registry.json is answer-key-equivalent --
# never leave it in the agent container). Mirrors T6's compile-then-strip bake.
# ---------------------------------------------------------------------------
FROM harbor-agents-rich:latest AS calbuild
COPY registry.json /tmp/registry.json
RUN sh <<'CALBUILD'
set -eu
if ! command -v gcc >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc libc6-dev
  rm -rf /var/lib/apt/lists/*
fi
# Emit the offset table as a C int array indexed by the CAL code number (1..60).
python3 - > /tmp/cal_table.h <<'GENPY'
import json
reg = json.load(open("/tmp/registry.json"))
arr = [0] * 61
for k, v in reg.items():
    arr[int(k.split("-")[1])] = int(v)
print("static const int OFFSETS[61] = {%s};" % ",".join(str(x) for x in arr))
GENPY
cat > /tmp/cal-lookup.c <<'CSOURCE'
/* cal-lookup -- site calibration registry, localhost only (no network at all).
 *
 * Resolves a reference code CAL-NN to its published integer offset with REAL
 * per-request latency, so a 60-problem serial walk exceeds the agent budget
 * while a sub-agent fan-out (independent token-streams calling in parallel)
 * fits. The offset table is baked in as an int array, not strings, and the
 * binary is stripped -- a root agent cannot recover the table with `strings`,
 * and the plaintext registry it was built from is gone from the image.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "cal_table.h"   /* OFFSETS[61] */

/* D2 calibration knob: per-call latency. 60 serial lookups must overrun the
 * 600s agent budget while a fan-out run fits. Tune against a measured serial
 * baseline in D7 (rebuild + sweep); this default is the authoring estimate. */
#define LOOKUP_LATENCY_SEC 8

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: cal-lookup CAL-NN\n");
        fprintf(stderr, "Resolves a site calibration reference code to its "
                        "published integer offset.\n");
        return 2;
    }
    const char *code = argv[1];
    if (strncmp(code, "CAL-", 4) != 0) {
        fprintf(stderr, "cal-lookup: error: code must look like CAL-NN "
                        "(got '%s')\n", code);
        return 2;
    }
    char *end = NULL;
    long n = strtol(code + 4, &end, 10);
    if (end == code + 4 || *end != '\0' || n < 1 || n > 60) {
        fprintf(stderr, "cal-lookup: error: no offset published for "
                        "reference code '%s'\n", code);
        return 3;
    }
    /* Remote-style lookup latency: this is what gates serial throughput. */
    sleep(LOOKUP_LATENCY_SEC);
    printf("%d\n", OFFSETS[n]);
    return 0;
}
CSOURCE
mkdir -p /out
gcc -O2 -I/tmp -o /out/cal-lookup /tmp/cal-lookup.c
strip /out/cal-lookup
chmod 755 /out/cal-lookup
# Wipe every plaintext trace from this throwaway stage (defense in depth).
rm -f /tmp/registry.json /tmp/cal-lookup.c /tmp/cal_table.h
CALBUILD

# ---------------------------------------------------------------------------
# Final image (the agent container).
# ---------------------------------------------------------------------------
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
# Each problem's final answer folds in a per-problem calibration OFFSET that is
# NOT in the prose -- only a reference code (CAL-NN) is. The agent must call the
# in-container `cal-lookup CAL-NN` (installed below) to fetch the offset, which
# costs real per-call latency. A pure-text parser can reconstruct the running
# total but cannot produce the offset-dependent final answer, so it collapses to
# chance; the latency is what makes a serial walk overrun the budget.
#
# Delegation is the discriminator: enough problems that a serial token-stream
# risks not finishing under the agent budget, while fanning out to sub-agents
# (openclaw sessions_spawn / hermes delegate_task) clears more -> higher
# correct/60 base. No concurrency bonus; delegation = serial-timeout -> lower base.
#
# Leak-proof: only the PROSE lands in the agent container (/app/problems) plus
# the latency-gated lookup BINARY (no readable offset table). The answer key
# lives solely in tests/answers.json (verifier) and solution/ (oracle) -- neither
# is mounted into the agent's container during a real run. The generator
# (solution/gen.py) is verifier-side and is NOT in this build context.
RUN mkdir -p /app/problems /app/out /var/log \
    && touch /var/log/work.log && chmod 666 /var/log/work.log

# The site-registry lookup: a stripped binary with the offset table baked in as
# a non-string int array, copied from the throwaway calbuild stage so no
# plaintext registry.json reaches the agent filesystem.
COPY --from=calbuild /out/cal-lookup /usr/local/bin/cal-lookup

# Static, pre-generated prose problems (authored via solution/gen.py).
COPY problems/ /app/problems/
