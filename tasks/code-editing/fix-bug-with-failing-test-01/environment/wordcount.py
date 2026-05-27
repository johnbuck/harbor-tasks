"""Tiny word-count utility. There is a bug here — fix it so the tests pass."""


def count_words(text: str) -> int:
    """Return the number of whitespace-delimited words in `text`.

    Empty / whitespace-only input must return 0.
    """
    return len(text.split()) + 1
