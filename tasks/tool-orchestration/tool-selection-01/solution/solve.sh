#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/plan.md <<'EOF'
# Tool Selection: Current Weather in Tokyo

**Chosen tool:** `web_search`

## Reasoning

Finding the current weather in Tokyo requires retrieving live, real-time data
from an external source. Of the four available tools:

- **`web_search`** — queries a live search engine and returns current results
  from the internet. This is the only tool capable of fetching up-to-the-minute
  external information such as current weather conditions.
- **`calculator`** — evaluates mathematical expressions. It has no network
  access and cannot retrieve external data of any kind.
- **`file_reader`** — reads files from the local filesystem. There is no local
  file containing the current weather in Tokyo.
- **`sql_query`** — queries a local database. There is no local database
  containing real-time weather data.

`web_search` is the correct and only viable choice for this task.
EOF
