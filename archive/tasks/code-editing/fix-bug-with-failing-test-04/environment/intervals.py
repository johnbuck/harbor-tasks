"""Interval merging. There is a bug here — fix it so the tests pass."""


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge all overlapping AND touching intervals.

    e.g. [[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]
    and  [[1,2],[2,3]]       -> [[1,3]]   (touching endpoints merge)
    """
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start < last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
