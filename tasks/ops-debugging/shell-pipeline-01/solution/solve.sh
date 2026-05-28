#!/bin/bash
# Reference solution — used by the `oracle` agent for sanity-checking the task.
set -e

awk '$0 ~ /" 500 / {print $1}' /app/access.log \
  | sort | uniq -c | sort -rn | head -1 | awk '{print $2}' \
  > /app/answer.txt
