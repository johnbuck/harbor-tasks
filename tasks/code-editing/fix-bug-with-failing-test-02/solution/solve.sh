#!/bin/bash
set -e

cat > /app/running_total.py <<'EOF'
"""Cumulative-sum utility."""


def running_total(nums: list[int]) -> list[int]:
    """Return a list where element i is the sum of nums[0..i] inclusive."""
    out: list[int] = []
    total = 0
    for i in range(0, len(nums)):
        total += nums[i]
        out.append(total)
    return out
EOF
