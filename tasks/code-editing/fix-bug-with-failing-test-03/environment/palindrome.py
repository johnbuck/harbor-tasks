"""Palindrome checker. There is a bug here — fix it so the tests pass."""


def is_palindrome(s: str) -> bool:
    """Return True if `s` reads the same forwards and backwards, ignoring
    case and any non-alphanumeric characters.
    """
    return s == s[::-1]
