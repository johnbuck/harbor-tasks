"""rewardkit grader for true-multi-turn-memory-write-01 / 08-recall-question.

8 personal fields recalled (latest-value-wins; two with stale-value exclusions) plus
a dinner that must respect the diet (no meat) and allergy (no unguarded peanut).
reward = (correct_fields/8) * (0.85 + 0.15*dinner_ok). The blend lives in a weight-1
`score` criterion; the 8 fields + dinner_ok + answer_present ride along weight-0.

D5 anchoring (kills false-zeros): each field maps to ONE labeled bullet in Part A
(by label, else by position among Part A bullets). Accept + stale-reject patterns run
ONLY on that line, so an honest recap that names the stale value elsewhere ("Timezone:
Mountain (was Pacific)", "Climbing nights: Mon/Wed/Fri — no longer Tue/Thu/Sat") is
not zeroed: a stale token counts as a leak only when it is NOT negated on its own line.
Dump-both ("Mon/Tue/Wed/Thu/Fri/Sat") still fails — that stale REJECT is the real
discriminator. Loose substrings tightened to word boundaries (`\bcat\b` so "delicate"
no longer over-credits the pet; `\bmira\b` so "mirage" no longer over-credits the
daughter). Dinner is graded over Part B only, so Part A text can't taint it.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

MEAT = (r'chicken|beef|pork|bacon|sausage|fish|salmon|tuna|shrimp|prawn|lamb|'
        r'turkey|duck|\bham\b|steak|carnitas|pancetta|prosciutto')

# Negation / contrast cues that mark a stale value as deliberately excluded.
NEG_CUE = re.compile(
    r"\bnot\b|n't|no longer|\bnever\b|rather than|instead of|as opposed to|"
    r"\bunlike\b|\bwas\b|\bwere\b|previously|formerly|used to|changed from|"
    r"moved from|switched from|\bold\b|\bavoid"
)


def _stale_leaked(cell: str, pat: str) -> bool:
    """True if a stale value is asserted on the line (present and NOT negated)."""
    for m in re.finditer(pat, cell):
        pre = cell[max(0, m.start() - 30):m.start()]
        if not NEG_CUE.search(pre):
            return True
    return False


@lru_cache(maxsize=4)
def _results(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "answer.md"
    raw = p.read_text() if p.exists() else ""
    if not raw.strip():
        return tuple({"cf": 0, "dinner_ok": 0, "answer_present": 0,
                      **{f: False for f in
                         ("f_diet", "f_pet", "f_timezone", "f_allergy", "f_hobby",
                          "f_climb_days", "f_coffee", "f_daughter")}}.items())

    lines = raw.split("\n")
    # Split Part A (the recap) from Part B (the dinner) on the first Part-B / dinner marker.
    pb = next((i for i, ln in enumerate(lines)
               if re.search(r'part\s*b|dinner', ln, re.I)), len(lines))
    part_a = lines[:pb] if pb < len(lines) else lines
    part_b = "\n".join(lines[pb:]).lower() if pb < len(lines) else raw.lower()

    bullets = [re.sub(r'^\s*[-*+\d.)\]]+\s*', '', ln).strip().lower()
               for ln in part_a
               if ln.strip() and not ln.strip().startswith('#')]

    def cell(idx: int, label: str) -> str:
        for b in bullets:
            if re.search(label, b):
                return b
        return bullets[idx - 1] if idx - 1 < len(bullets) else ""

    tz = cell(3, r'time\s*zone|timezone')
    climb = cell(6, r'climb\w*\s*(?:night|day|session|schedul)')

    fields = {
        "f_diet": bool(re.search(r'vegetarian|lacto-ovo|lacto ovo', cell(1, r'\bdiet\b'))),
        "f_pet": (lambda c: bool(re.search(r'\bsushi\b', c)) and bool(re.search(r'\bcat\b', c)))(cell(2, r'\bpet\b')),
        "f_timezone": (bool(re.search(r'mountain time|mountain \(|america/denver|mt \(|denver|\bmt\b|\bmst\b|\bmdt\b', tz))
                       and not _stale_leaked(tz, r'pacific|\bpst\b|\bpdt\b|\bpt\b')),
        "f_allergy": bool(re.search(r'\bpeanut', cell(4, r'allerg'))),
        "f_hobby": bool(re.search(r'boulder|climb', cell(5, r'\bhobby\b'))),
        "f_climb_days": (bool(re.search(r'\bmon(?:day)?\b', climb))
                         and bool(re.search(r'\bwed(?:nesday)?\b', climb))
                         and bool(re.search(r'\bfri(?:day)?\b', climb))
                         and not _stale_leaked(
                             climb, r'\btues?(?:day)?\b|\bthur?s?(?:day)?\b|\bsat(?:urday)?\b')),
        "f_coffee": (lambda c: bool(re.search(r'\boat', c)) and bool(re.search(r'latte|coffee', c)))(cell(7, r'coffee')),
        "f_daughter": bool(re.search(r'\bmira\b', cell(8, r'daughter'))),
    }
    cf = sum(1 for v in fields.values() if v)

    veg = 0 if re.search(MEAT, part_b) else 1
    peanut = 1
    if re.search('peanut', part_b):
        if (re.search(r'peanut (sauce|butter|oil|noodle|dressing)', part_b)
                and not re.search(r'(no|without|skip|avoid|free of|free from|instead of) peanut|peanut[- ]free', part_b)):
            peanut = 0
    dinner_ok = veg * peanut
    return tuple({"cf": cf, "dinner_ok": dinner_ok, "answer_present": 1, **fields}.items())


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    r = dict(_results(str(workspace)))
    if key == "score":
        return (r["cf"] / 8.0) * (0.85 + 0.15 * r["dinner_ok"])
    if key in ("dinner_ok", "answer_present"):
        return bool(r[key])
    return bool(r[key])


rk.check("score", "reward = (correct_fields/8)*(0.85+0.15*dinner_ok)", weight=1.0)
for _k, _l in [("f_diet", "diet"), ("f_pet", "pet"),
               ("f_timezone", "timezone (current, not pacific)"),
               ("f_allergy", "allergy"), ("f_hobby", "hobby"),
               ("f_climb_days", "climb days M/W/F (not T/Th/Sa)"),
               ("f_coffee", "coffee"), ("f_daughter", "daughter"),
               ("dinner_ok", "dinner respects diet + allergy"),
               ("answer_present", "answer persisted (VOID vs present-but-wrong)")]:
    rk.check(_k, _l, weight=0.0)
