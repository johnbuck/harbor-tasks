#!/bin/bash
# CHEAT-PROOF MEMORY GATE: wipe records + agent scratch before recall, so each
# chained answer comes from in-context memory, not a re-read. (Corpus FITS the
# window -> rot test, not eviction: what's measured is whether the harness still
# holds BOTH hops of each chain across a long context.)
rm -rf /app/reports 2>/dev/null || true
find /app -mindepth 1 -delete 2>/dev/null || true
