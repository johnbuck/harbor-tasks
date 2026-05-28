#!/bin/bash
set -e

cat > /app/intervals.py <<'EOF'
"""Interval merging."""


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge all overlapping AND touching intervals."""
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
EOF
