#!/bin/bash
# Graded verifier (rewardkit) for web-research-multi-page.
#
# reward = 1.0 iff /app/answer.txt names the author the SITE attributes the quote
# to (Jim Henson) AND does not also name a decoy author from the same page (a
# sibling penalty) AND the trajectory shows a real browser tool call. Content-
# matched + format-tolerant so a content-correct answer is never falsely zeroed.
# The headline is carried by the weight-1 `score` criterion; the answer sub-checks
# and the browser-used gate are weight-0 detail (-> reward-details.json).
#
# reward is GATED on actually using the browser: a correct answer obtained WITHOUT
# the browser (from memorized quotes.toscrape data, or a curl-bypass) does NOT
# count. Browser-tool calls are matched for BOTH harness conventions (openclaw's
# single `browser` tool and hermes's `browser_navigate`/...).
#
# ORACLE CAVEAT: the oracle isn't a browser, so it gets answer_correct=1 but
# browser_used=0 -> headline reward 0. That is EXPECTED — a browser-required task
# can't be end-to-end oracle-proven; the oracle validates the answer-checking
# sub-field, a real n=1 proves the browser path.
set -u
mkdir -p /logs/verifier

# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
