#!/bin/bash
# Graded PROACTIVE-preference application. The trigger task never restated the
# standing preferences (ISO dates / 24h time / no-emoji headings / D.H. sign-off)
# and even phrased the date+time in the NON-preferred form ("March 5th ... 3:00
# PM"). reward = fraction of the 4 standing preferences the harness applied on
# its own. A harness that simply echoes the literal task scores low; one whose
# memory surfaces the preferences unprompted scores high.
mkdir -p /logs/verifier
python3 - <<'PY' > /logs/verifier/reward.json
import json, re
try:
    txt = open("/app/announce.md").read()
except Exception:
    print(json.dumps({"reward":0.0,"correctness":0,"prefs_applied":0,"prefs_total":4,
                      "file_present":0,"iso_date":0,"time_24h":0,"no_emoji_title":0,"signoff_dh":0}))
    raise SystemExit

def is_emoji(ch):
    o = ord(ch)
    return ((0x1F000 <= o <= 0x1FAFF) or (0x2600 <= o <= 0x27BF) or
            (0x2B00 <= o <= 0x2BFF) or o in (0xFE0F,0x203C,0x2049,0x2122,0x2139) or
            (0x1F1E6 <= o <= 0x1F1FF))

checks = {}
# 1. date applied as ISO 8601 (proactive: task said "March 5th, 2026")
checks["iso_date"] = bool(re.search(r"\b2026-03-05\b", txt))
# 2. time on 24h clock (proactive: task said "3:00 PM")
checks["time_24h"] = bool(re.search(r"\b15:00\b", txt))
# 3. no emoji in the heading/title line
lines = [l for l in txt.splitlines() if l.strip()]
heads = [l for l in txt.splitlines() if l.lstrip().startswith("#")] or (lines[:1] if lines else [])
checks["no_emoji_title"] = not any(is_emoji(c) for l in heads for c in l)
# 4. signed off with the operator's initials D.H.
checks["signoff_dh"] = bool(re.search(r"\bD\.\s?H\.?", txt))

s = sum(1 for v in checks.values() if v)
print(json.dumps({
    "reward": round(s/4, 4),
    "correctness": 1 if s == 4 else 0,
    "prefs_applied": s, "prefs_total": 4, "file_present": 1,
    "iso_date": int(checks["iso_date"]), "time_24h": int(checks["time_24h"]),
    "no_emoji_title": int(checks["no_emoji_title"]), "signoff_dh": int(checks["signoff_dh"]),
}))
PY
