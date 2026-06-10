"""rewardkit grader for multistep-proactive-preference-01 / 04-announce.

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
    txt = p.read_text() if p.exists() else ""
    lines = [l for l in txt.splitlines() if l.strip()]
    heads = [l for l in txt.splitlines() if l.lstrip().startswith("#")] or (lines[:1] if lines else [])
    return tuple({
        "iso_date": bool(re.search(r"\b2026-03-05\b", txt)),
        "time_24h": bool(re.search(r"\b15:00\b", txt)),
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
