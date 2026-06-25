"""rewardkit grader for apply-standing-preferences-unprompted / 04-announce.

Proactive application of 4 stated preferences to /app/announce.md: ISO date,
24h time, no emoji in the title, and a "D.H." sign-off. reward = applied/4.
One criterion per preference (same checks as the prior grader).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk


def _is_emoji(ch: str) -> bool:
    o = ord(ch)
    return ((0x1F000 <= o <= 0x1FAFF) or (0x2600 <= o <= 0x27BF) or
            (0x2B00 <= o <= 0x2BFF) or o in (0xFE0F, 0x203C, 0x2049, 0x2122, 0x2139) or
            (0x1F1E6 <= o <= 0x1F1FF))


@lru_cache(maxsize=4)
def _checks(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "announce.md"
    txt = p.read_text(errors="replace") if p.exists() else ""
    lines = [l for l in txt.splitlines() if l.strip()]
    heads = [l for l in txt.splitlines() if l.lstrip().startswith("#")] or (lines[:1] if lines else [])
    low = txt.lower()
    # A pref passes only if the PREFERRED form is present AND the non-preferred
    # form is absent: keeping both (a hedge) does not apply the preference.
    iso_ok = bool(re.search(r"\b2026-03-05\b", txt)) and not re.search(
        r"march\s*5(th)?\b|\bmar\s*5(th)?\b|\b3/5\b|\b03/05\b", low)
    t24_ok = bool(re.search(r"\b15:00\b", txt)) and not re.search(
        r"3:?00\s*pm|\b3\s*pm\b", low)
    return tuple({
        "iso_date": iso_ok,
        "time_24h": t24_ok,
        "no_emoji_title": not any(_is_emoji(c) for l in heads for c in l),
        "signoff_dh": bool(re.search(r"\bD\.\s?H\.?", txt)),
    }.items())


@rk.criterion(description="{label}")
def pref(workspace: Path, key: str, label: str) -> bool:
    return dict(_checks(str(workspace)))[key]


for _k, _l in [("iso_date", "ISO date 2026-03-05"),
               ("time_24h", "24h time 15:00"),
               ("no_emoji_title", "no emoji in the title"),
               ("signoff_dh", "sign-off 'D.H.'")]:
    rk.pref(_k, _l)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "announce.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)
