#!/bin/bash
# Oracle ingest: an attentive analyst reads the week's report. No file artefact
# is produced (notes are forbidden); the final recall step supplies the answers.
cat /app/reports/week_01.txt > /dev/null 2>&1 || true
exit 0
