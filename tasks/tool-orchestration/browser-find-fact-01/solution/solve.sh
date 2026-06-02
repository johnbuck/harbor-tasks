#!/bin/bash
# Oracle: writes the site's attribution for the asked quote. (The oracle is not a
# browser, so it only validates the GRADER plumbing — the end-to-end browser path
# is proven by a real LLM n=1, not by this.) On https://quotes.toscrape.com/js/
# page 3, "...give a stupid or misinformed beholder a black eye" is attributed to
# Jim Henson.
set -u
mkdir -p /app
echo "Jim Henson" > /app/answer.txt
