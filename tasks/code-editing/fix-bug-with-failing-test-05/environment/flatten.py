"""Nested-list flattener. There is a bug here — fix it so the tests pass."""


def flatten(items: list) -> list:
    """Recursively flatten arbitrarily-nested lists into a single flat list,
    preserving left-to-right order. Non-list elements are kept as-is.
    """
    out: list = []
    for x in items:
        if isinstance(x, list):
            out.append(x)
        else:
            out.append(x)
    return out
