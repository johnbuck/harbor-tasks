#!/bin/bash
# Deterministic graded verifier for factual-lookup-cited-01 (HARD, corpus-based).
#
# Ten factual questions about the fictional "Halcyon Systems" knowledge base
# (served at localhost:8780). Each fact has a CURRENT authoritative page and an
# ARCHIVED/legacy near-duplicate page that states a superseded/wrong value.
#
# An item earns credit ONLY when, within its numbered block, BOTH:
#   (a) the CURRENT/correct value appears, AND
#   (b) a source URL cites the AUTHORITATIVE page path AND does NOT rely on the
#       archived near-duplicate path.
# Citing the archive page (even with the right value) scores 0 for that item.
# Stating the archive's wrong value scores 0 for that item.
#
# Scoring (graded fraction, NOT binary):
#   found       = # items fully correct (value + authoritative citation)
#   reward      = round(found / 10, 4)
#   correctness = 1 iff found == 10 else 0

set -u
mkdir -p /logs/verifier
TARGET=/app/answer.md

if [ ! -f "$TARGET" ]; then
  echo '{"reward": 0.0, "correctness": 0, "found": 0, "total": 10, "missing_answer": 1}' > /logs/verifier/reward.json
  exit 0
fi

python3 - "$TARGET" <<'PY'
import json, re, sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
if not text.strip():
    json.dump({"reward": 0.0, "correctness": 0, "found": 0, "total": 10, "empty_answer": 1},
              open("/logs/verifier/reward.json", "w"))
    sys.exit(0)

# Split into per-item blocks on leading "N." / "N)" markers (1..10).
parts = re.split(r'(?m)^\s*(10|[1-9])[\.\)]\s', text)
blocks = {}
for i in range(1, len(parts) - 1, 2):
    n = int(parts[i])
    blocks[n] = parts[i + 1]

# (value_regex, good_path_substr, bad_path_substr, bad_value_regex)
# good_path must appear in some URL in the block; bad_path must NOT be the only
# cited source; bad_value (the archive's wrong value), if present, voids the item.
checks = {
    1:  (r'\b2013\b',            '/about.html',                          '/press/2019-profile.html',          r'\b2011\b'),
    2:  (r'priya|nandakumar',    '/team/leadership.html',                '/archive/team-2018.html',           r'tom reyes|reyes'),
    3:  (r'tallinn',             '/about.html',                          '/press/2019-profile.html',          r'helsinki'),
    4:  (r'aperture',            '/products/index.html',                 '/products/legacy.html',             r'\bbeacon\b'),
    5:  (r'\b7\.2\b',            '/products/aperture/releases.html',     '/products/aperture/changelog-archive.html', r'\b5\.4\b'),
    6:  (r'\b480\b',             '/about.html',                          '/press/2019-profile.html',          r'\b300\b'),
    7:  (r'\b62\b',              '/investors/fy2025.html',               '/investors/fy2023.html',            r'\b41\b'),
    8:  (r'support@halcyon',     '/contact.html',                        '/archive/contact-old.html',         r'help@halcyon'),
    9:  (r'frankfurt',           '/infra/regions.html',                  '/infra/regions-2020.html',          r'dublin'),
    10: (r'\b1000\b|1,000',      '/docs/api/limits.html',                '/docs/api/limits-v1.html',          r'\b500\b'),
}

URL = re.compile(r'https?://\S+')

per = {}
found = 0
for n in range(1, 11):
    body = blocks.get(n, "")
    low = body.lower()
    vrx, good, bad, badval = checks[n]
    val_ok = bool(re.search(vrx, low))
    badval_present = bool(re.search(badval, low))
    urls = [u.lower().rstrip('.,);') for u in URL.findall(body)]
    cites_good = any(good in u for u in urls)
    cites_bad  = any(bad in u for u in urls)
    # Credit requires: correct value, NOT asserting the wrong archived value,
    # cites the authoritative page, and does not cite ONLY the archive page.
    ok = 1 if (val_ok and not badval_present and cites_good and not (cites_bad and not cites_good)) else 0
    # Note: cites_good already true means at least the right page is cited; if the
    # block also cites the bad page that's tolerated as long as the good page is
    # present AND the wrong value isn't asserted.
    if cites_bad and not cites_good:
        ok = 0
    per[f"item{n}"] = ok
    found += ok

reward = round(found / 10.0, 4)
correctness = 1 if found == 10 else 0
out = {"reward": reward, "correctness": correctness, "found": found, "total": 10}
out.update(per)
json.dump(out, open("/logs/verifier/reward.json", "w"))
print(json.dumps(out))
PY
