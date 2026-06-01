#!/bin/bash
# Reference solution — implements the FULL contract (overlap+touching+containment
# merge, input not mutated, ValueError on start>end). Scores 1.0.
set -e

cat > /app/intervals.py <<'EOF'
"""Interval merging implementing the merge_intervals contract."""


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping, touching, and contained closed integer intervals.

    The input is not mutated (new inner lists are returned). An interval with
    start > end is invalid and raises ValueError; zero-width [x, x] is valid.
    """
    for iv in intervals:
        if iv[0] > iv[1]:
            raise ValueError(f"invalid interval: {iv!r}")
    if not intervals:
        return []
    ordered = sorted((list(iv) for iv in intervals), key=lambda iv: (iv[0], iv[1]))
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
EOF
