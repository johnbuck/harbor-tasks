"""rewardkit grader for agentic-research-with-memory-01 — 8 cited facts about
Mirador Labs.

A fact matches when some unit (paragraph or sentence) of /app/brief.md states the
CORRECT value, carries a markdown link to an AUTHORITATIVE page, and does not also
assert a known-wrong value. reward = matched/8. Same logic/patterns as the prior
inline grader, restructured as one parametrized rewardkit criterion (per FOOTGUNS
#45, never a zero-arg criterion).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# key: (value_regex, authoritative_paths, wrong_value_regex|None); f6 is special.
FACTS = {
    "f1_founded":      (r'\b2024\b',                   ['/about.html'],                                              r'\b2021\b'),
    "f2_hq":           (r'san francisco',              ['/about.html'],                                              r'berkeley'),
    "f3_climate_lead": (r'petra holm|holm',            ['/people.html', '/research/climate.html'],                   r'yusra chen|chen'),
    "f4_nsf_total":    (r'\$?\s*5\.3\s*(m|million)',   ['/funding.html', '/research/climate.html', '/research/neural.html'], None),
    "f5_pubs":         (r'\b18\b|eighteen',            ['/publications/2025.html'],                                  r'\b23\b|twenty'),
    "f6_partners":     None,  # special: >=2 of UCSF/BioGen/NCAR + partners.html link in one unit
    "f7_staff":        (r'\b23\b',                     ['/careers.html'],                                            r'\b40\b|forty'),
    "f8_gpus":         (r'\b12\b',                     ['/research/neural.html'],                                    r'\b24\b|twenty[- ]?four'),
}
LABELS = {
    "f1_founded": "founded 2024 (not 2021)",
    "f2_hq": "HQ San Francisco (not Berkeley)",
    "f3_climate_lead": "climate lead Petra Holm (not Chen)",
    "f4_nsf_total": "2025 NSF total $5.3M (synthesis)",
    "f5_pubs": "18 publications (not 23)",
    "f6_partners": "two partners (>=2 of UCSF/BioGen/NCAR, cited)",
    "f7_staff": "23 full-time staff (not 40)",
    "f8_gpus": "12 H100 GPUs (not 24)",
}


def _brief(workspace: Path) -> str:
    p = workspace / "brief.md"
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


@lru_cache(maxsize=4)
def _units(brief_text: str) -> tuple:
    """Paragraphs plus sentence splits — tightens value<->citation locality."""
    units = []
    for blk in re.split(r'\n\s*\n', brief_text):
        units.append(blk)
        for sent in re.split(r'(?<=[.!?])\s+', blk):
            units.append(sent)
    return tuple(u for u in units if u.strip())


def _md_links(s: str) -> set:
    return {m.lower() for m in re.findall(r'\]\((/[^)]+?)\)', s)}


def _fact_match(units, value_rx, good_paths, bad_value_rx=None) -> bool:
    vrx = re.compile(value_rx, re.I)
    good = {p.lower() for p in good_paths}
    badrx = re.compile(bad_value_rx, re.I) if bad_value_rx else None
    for u in units:
        if not vrx.search(u):
            continue
        if badrx and badrx.search(u):
            continue
        if _md_links(u) & good:
            return True
    return False


def _partners(units) -> bool:
    for u in units:
        ul = u.lower()
        cnt = sum(1 for p in ('ucsf', 'biogen', 'ncar') if p in ul)
        if cnt >= 2 and '/partners.html' in _md_links(u):
            return True
    return False


@rk.criterion(description="{label}")
def fact(workspace: Path, key: str, label: str) -> bool:
    units = _units(_brief(workspace))
    if key == "f6_partners":
        return _partners(units)
    value_rx, good_paths, bad_value_rx = FACTS[key]
    return _fact_match(units, value_rx, good_paths, bad_value_rx)


for _key, _label in LABELS.items():
    rk.fact(_key, _label)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "brief.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)
