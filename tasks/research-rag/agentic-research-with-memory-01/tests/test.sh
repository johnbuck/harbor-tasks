#!/bin/bash
# Deterministic graded verifier for agentic-research-with-memory-01 (HARD).
#
# Eight facts about Mirador Labs. Each fact earns credit ONLY when, within the
# same sentence/paragraph, the brief states the CORRECT value AND carries a
# markdown citation to the AUTHORITATIVE page that supports it.
#
# Difficulty wrinkles:
#   - press.html is a third-party profile with plausible-but-WRONG values
#     (founded 2021, Berkeley HQ, climate lead "Chen", $4.2M NSF total, 40 staff,
#     24 GPUs, "twenty+" pubs). Citing press.html (or stating its wrong value)
#     earns no credit for that fact.
#   - publications/drafts.html lists a 23-item pipeline tally; the published
#     count is 18.
#   - The 2025 NSF total is a SYNTHESIS: $4.2M (climate) + $1.1M (neural) = $5.3M.
#     The DOE $2.5M quantum award and the 2024 NSF $3.0M award must be excluded.
#
# Scoring (graded fraction, NOT binary):
#   matched     = # of the 8 facts where (correct value AND correct-page citation
#                  appear in the same paragraph)
#   reward      = round(matched / 8, 4)           (float 0..1)
#   correctness = 1 iff matched == 8 else 0
#
# A small no-hallucination guard: parroting the press page's wrong founding year
# (2021) or wrong NSF total ($4.2M total / $40 staff) does not match the
# corresponding fact regex, so it scores 0 for that fact automatically.

set -u
mkdir -p /logs/verifier
BRIEF=/app/brief.md

if [ ! -f "$BRIEF" ]; then
  echo '{"reward": 0.0, "correctness": 0, "matched": 0, "total": 8, "missing_brief": 1}' > /logs/verifier/reward.json
  exit 0
fi

python3 - "$BRIEF" <<'PY'
import json, re, sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
if not text.strip():
    json.dump({"reward": 0.0, "correctness": 0, "matched": 0, "total": 8, "empty_brief": 1},
              open("/logs/verifier/reward.json", "w"))
    sys.exit(0)

low = text.lower()

# Split into paragraphs on blank lines; also treat each markdown bullet / line as
# its own unit so a single dense paragraph still yields per-sentence locality.
para_blocks = re.split(r'\n\s*\n', text)
units = []
for blk in para_blocks:
    units.append(blk)
    # Also add sentence-ish splits to tighten value<->citation locality.
    for sent in re.split(r'(?<=[.!?])\s+', blk):
        units.append(sent)
units = [u for u in units if u.strip()]

def md_links(s):
    # returns set of cited paths like /about.html
    return set(m.lower() for m in re.findall(r'\]\((/[^)]+?)\)', s))

# A fact matches if SOME unit contains the value regex AND a markdown link whose
# path is in `good_paths` AND (if bad_paths given) does NOT rely solely on a
# bad-path link for that same unit.
def fact_match(value_rx, good_paths, bad_value_rx=None):
    vrx = re.compile(value_rx, re.I)
    good = set(p.lower() for p in good_paths)
    badrx = re.compile(bad_value_rx, re.I) if bad_value_rx else None
    for u in units:
        if not vrx.search(u):
            continue
        if badrx and badrx.search(u):
            # the unit also asserts a known-wrong value -> ambiguous, skip
            continue
        links = md_links(u)
        if links & good:
            return 1
    return 0

# ---- 8 facts ----
# 1. founded 2024 (NOT 2021)
f1 = fact_match(r'\b2024\b', ['/about.html'], bad_value_rx=r'\b2021\b')
# 2. HQ San Francisco (NOT Berkeley)
f2 = fact_match(r'san francisco', ['/about.html'], bad_value_rx=r'berkeley')
# 3. climate lead Petra Holm (NOT Chen) — cite people.html or climate.html
f3 = fact_match(r'petra holm|holm', ['/people.html', '/research/climate.html'],
                bad_value_rx=r'yusra chen|chen')
# 4. total NSF 2025 == 5.3M (synthesis). Accept "5.3" million; reject 4.2-only / 9.8 / 3.0
f4 = fact_match(r'\$?\s*5\.3\s*(m|million)', ['/funding.html', '/research/climate.html', '/research/neural.html'])
# 5. 18 publications (NOT 23 / twenty)
f5 = fact_match(r'\b18\b', ['/publications/2025.html'], bad_value_rx=r'\b23\b|twenty')
# 6. two partners — require partners.html link AND >=2 of UCSF/BioGen/NCAR in same unit
def partners_match():
    for u in units:
        ul = u.lower()
        cnt = sum(1 for p in ('ucsf', 'biogen', 'ncar') if p in ul)
        if cnt >= 2 and ('/partners.html' in md_links(u)):
            return 1
    return 0
f6 = partners_match()
# 7. 23 full-time staff (NOT 40) — cite careers.html
f7 = fact_match(r'\b23\b', ['/careers.html'], bad_value_rx=r'\b40\b|forty')
# 8. 12 H100 GPUs (NOT 24) — cite research/neural.html
f8 = fact_match(r'\b12\b', ['/research/neural.html'], bad_value_rx=r'\b24\b|twenty[- ]?four')

matched = f1 + f2 + f3 + f4 + f5 + f6 + f7 + f8
reward = round(matched / 8.0, 4)
correctness = 1 if matched == 8 else 0

out = {
    "reward": reward, "correctness": correctness, "matched": matched, "total": 8,
    "f1_founded": f1, "f2_hq": f2, "f3_climate_lead": f3, "f4_nsf_total": f4,
    "f5_pubs": f5, "f6_partners": f6, "f7_staff": f7, "f8_gpus": f8,
}
json.dump(out, open("/logs/verifier/reward.json", "w"))
print(json.dumps(out))
PY
