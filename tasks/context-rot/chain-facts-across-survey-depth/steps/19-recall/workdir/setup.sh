#!/bin/bash
# CHEAT-PROOF MEMORY GATE: wipe records + agent scratch before recall, so each
# chained answer comes from in-context memory, not a re-read. (Corpus FITS the
# window -> rot test, not eviction: what's measured is whether the harness still
# holds BOTH hops of each chain across a long context.)
source "$(dirname "$0")/wipe_scratch.sh"
rm -rf /app/reports 2>/dev/null
find /app -mindepth 1 -delete 2>/dev/null
