"""Acceptance guard for the unified suite (2026-06-25-unify-full-suite.md).

FAILS if the retired core/non-core + Track-A/Track-B framing reappears in live
SOURCE. The suite is ONE set under ONE bar; the old tier vocabulary is retired.

Scope (matches the spec's "live tree, excluding backlog/ + archive/"):
  - tracked source files only (git ls-files), .py/.md/.yaml/.yml/.toml/.sh
  - EXCLUDES backlog/ + archive/ (dated historical record, kept verbatim)
  - EXCLUDES .serena/ (tool-managed memory) and generated *.html
  - EXCLUDES this guard file itself (it names the tokens it bans)
  - dated spec-slug citations (YYYY-MM-DD-...[.md], with or without the .md) are
    allowed pointers to the historical record (item 7 keeps backlog filenames +
    facts): each line has its slug tokens stripped before matching.
"""
import re
import subprocess

from helpers import REPO_ROOT

LEGACY = re.compile(
    r"core[ -]eleven|non-?core|"
    r"track-[ab]\b|"            # hyphenated track-a / track-b (framing, any case)
    r"(?-i:Track [AB])\b|"      # space form: capitalized only (not 'track a file')
    r"\btrack_a\b|core-suite|core_suite|run_track_a|oracle-core|track_a_report",
    re.IGNORECASE,
)
SPEC_SLUG = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+(?:\.md)?")
EXTS = ("*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.sh")
EXCLUDE_PREFIX = ("backlog/", "archive/", ".serena/")
SELF = "tests/hygiene/test_suite_no_legacy_framing.py"


def _tracked():
    out = subprocess.check_output(
        ["git", "ls-files", *EXTS], cwd=str(REPO_ROOT), text=True)
    for rel in out.splitlines():
        if rel == SELF or rel.startswith(EXCLUDE_PREFIX):
            continue
        yield rel


def test_no_legacy_tiering_framing_in_live_source():
    offenders = []
    for rel in _tracked():
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = SPEC_SLUG.sub("", line)
            if LEGACY.search(stripped):
                offenders.append(f"{rel}:{i}: {line.strip()[:110]}")
    assert not offenders, (
        "retired core/non-core / Track-A/Track-B framing reappeared in live "
        "source (see backlog/2026-06-25-unify-full-suite.md). Offenders:\n  "
        + "\n  ".join(offenders))
