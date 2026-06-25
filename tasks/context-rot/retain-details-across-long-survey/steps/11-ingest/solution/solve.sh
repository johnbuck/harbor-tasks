#!/bin/bash
# Oracle ingest: an attentive surveyor reads the week's record. No artefact is
# produced (no notes); the final recall step supplies the answers.
cat /app/reports/week_11.txt > /dev/null 2>&1 || true
exit 0
