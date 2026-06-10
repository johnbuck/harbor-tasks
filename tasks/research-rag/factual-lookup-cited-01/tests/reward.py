"""rewardkit grader for factual-lookup-cited-01 — 10 cited-fact items.

Ten factual questions about the fictional "Halcyon Systems" KB. Each item earns
credit ONLY when, within its numbered block: the CURRENT value appears, the
ARCHIVE's wrong value does NOT, an authoritative page is cited, and the block
does not rely solely on the archived near-duplicate. reward = found/10. Same
match patterns as the prior bash grader, restructured as one criterion per item.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# (value_regex, authoritative_path, archive_path, archive_wrong_value_regex)
CHECKS = {
    1:  (r'\b2013\b',          '/about.html',                      '/press/2019-profile.html',          r'\b2011\b'),
    2:  (r'priya|nandakumar',  '/team/leadership.html',            '/archive/team-2018.html',           r'tom reyes|reyes'),
    3:  (r'tallinn',           '/about.html',                      '/press/2019-profile.html',          r'helsinki'),
    4:  (r'aperture',          '/products/index.html',             '/products/legacy.html',             r'\bbeacon\b'),
    5:  (r'\b7\.2\b',          '/products/aperture/releases.html', '/products/aperture/changelog-archive.html', r'\b5\.4\b'),
    6:  (r'\b480\b',           '/about.html',                      '/press/2019-profile.html',          r'\b300\b'),
    7:  (r'\b62\b',            '/investors/fy2025.html',           '/investors/fy2023.html',            r'\b41\b'),
    8:  (r'support@halcyon',   '/contact.html',                    '/archive/contact-old.html',         r'help@halcyon'),
    9:  (r'frankfurt',         '/infra/regions.html',              '/infra/regions-2020.html',          r'dublin'),
    10: (r'\b1000\b|1,000',    '/docs/api/limits.html',            '/docs/api/limits-v1.html',          r'\b500\b'),
}
URL = re.compile(r'https?://\S+')


@lru_cache(maxsize=4)
def _blocks(answer_text: str) -> tuple:
    """Split answer.md into per-item blocks on leading 'N.' / 'N)' markers."""
    parts = re.split(r'(?m)^\s*(10|[1-9])[\.\)]\s', answer_text)
    blocks = {}
    for i in range(1, len(parts) - 1, 2):
        blocks[int(parts[i])] = parts[i + 1]
    return tuple(sorted(blocks.items()))


def _block(workspace: Path, n: int) -> str:
    p = workspace / "answer.md"
    if not p.exists():
        return ""
    return dict(_blocks(p.read_text(encoding="utf-8", errors="replace"))).get(n, "")


@rk.criterion(description="item {n}: correct value + authoritative citation")
def item(workspace: Path, n: int) -> bool:
    body = _block(workspace, n)
    low = body.lower()
    value_rx, good_path, bad_path, bad_value_rx = CHECKS[n]
    value_ok = bool(re.search(value_rx, low))
    wrong_value_present = bool(re.search(bad_value_rx, low))
    urls = [u.lower().rstrip('.,);') for u in URL.findall(body)]
    cites_authoritative = any(good_path in u for u in urls)
    cites_archive = any(bad_path in u for u in urls)
    # Credit: correct value, not the archive's wrong value, cites the
    # authoritative page, and doesn't rely solely on the archive.
    if not (value_ok and not wrong_value_present and cites_authoritative):
        return False
    if cites_archive and not cites_authoritative:
        return False
    return True


for _n in range(1, 11):
    rk.item(_n)
