"""Cumulative-sum utility. There is a bug here — fix it so the tests pass."""


def running_total(nums: list[int]) -> list[int]:
    """Return a list where element i is the sum of nums[0..i] inclusive.

    Empty input returns an empty list.
    """
    out: list[int] = []
    total = 0
    for i in range(1, len(nums)):
        total += nums[i]
        out.append(total)
    return out
