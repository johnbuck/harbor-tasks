"""rewardkit grader for true-multi-turn-memory-write-01 / 08-recall-question.

8 personal fields recalled (latest-value-wins; some with sibling exclusions) plus a
dinner that must respect the diet (no meat) and allergy (no unguarded peanut).
reward = (correct_fields/8) * (0.85 + 0.15*dinner_ok). Same has/no patterns as the
prior bash grader; the blend formula lives in a weight-1 `score` criterion, the 8
fields + dinner_ok ride along weight-0.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

MEAT = (r'chicken|beef|pork|bacon|sausage|fish|salmon|tuna|shrimp|prawn|lamb|'
        r'turkey|duck|\bham\b|steak|carnitas|pancetta|prosciutto')


@lru_cache(maxsize=4)
def _results(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "answer.md"
    if not p.exists() or not p.read_text().strip():
        return tuple({"cf": 0, "dinner_ok": 0, **{f: False for f in
                      ("f_diet", "f_pet", "f_timezone", "f_allergy", "f_hobby",
                       "f_climb_days", "f_coffee", "f_daughter")}}.items())
    ans = p.read_text().lower()

    def has(pat: str) -> bool:
        return re.search(pat, ans) is not None

    fields = {
        "f_diet": has(r'vegetarian|lacto-ovo|lacto ovo'),
        "f_pet": has('sushi') and has('cat'),
        "f_timezone": (has(r'mountain time|mountain \(|america/denver|mt \(|denver|\bmt\b|\bmst\b|\bmdt\b')
                       and not has(r'timezone[^a-z]*[:=-]?[^a-z]*pacific|pacific time|currently.*pacific|on pacific|\bpt\b|\bpst\b|\bpdt\b')),
        "f_allergy": has('peanut'),
        "f_hobby": has(r'boulder|climb'),
        "f_climb_days": (has('monday') and has('wednesday') and has('friday')
                         and not has(r'tuesday|thursday|saturday')),
        "f_coffee": has('oat') and has(r'latte|coffee'),
        "f_daughter": has('mira'),
    }
    cf = sum(1 for v in fields.values() if v)
    veg = 0 if has(MEAT) else 1
    peanut = 1
    if has('peanut'):
        if (has(r'peanut (sauce|butter|oil|noodle|dressing)')
                and not has(r'(no|without|skip|avoid|free of|free from|instead of) peanut|peanut[- ]free')):
            peanut = 0
    dinner_ok = veg * peanut
    return tuple({"cf": cf, "dinner_ok": dinner_ok, **fields}.items())


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    r = dict(_results(str(workspace)))
    if key == "score":
        return (r["cf"] / 8.0) * (0.85 + 0.15 * r["dinner_ok"])
    if key == "dinner_ok":
        return bool(r["dinner_ok"])
    return bool(r[key])


rk.check("score", "reward = (correct_fields/8)*(0.85+0.15*dinner_ok)", weight=1.0)
for _k, _l in [("f_diet", "diet"), ("f_pet", "pet"),
               ("f_timezone", "timezone (current, not pacific)"),
               ("f_allergy", "allergy"), ("f_hobby", "hobby"),
               ("f_climb_days", "climb days M/W/F (not T/Th/Sa)"),
               ("f_coffee", "coffee"), ("f_daughter", "daughter"),
               ("dinner_ok", "dinner respects diet + allergy")]:
    rk.check(_k, _l, weight=0.0)
