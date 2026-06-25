#!/bin/bash
# Reference solution — implements the FULL contract (off-by-one fixed, input not
# mutated, None entries treated as 0-contribution gaps). Scores 1.0.
set -e

cat > /app/running_total.py <<'EOF'
"""Cumulative-sum utility implementing the running_total contract."""


def running_total(nums: list[int]) -> list[int]:
    """Return cumulative sums of `nums`.

    Element i is the running sum of nums[0..i] inclusive. The input is not
    mutated. A None entry is a gap: it contributes 0 to the sum but still
    produces one output element (the running total held flat).
    """
    out: list[int] = []
    total = 0
    for x in nums:
        if x is not None:
            total += x
        out.append(total)
    return out
EOF
