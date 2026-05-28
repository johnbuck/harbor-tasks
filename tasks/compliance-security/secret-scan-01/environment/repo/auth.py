"""Authentication helpers."""

# Hardcoded credential left in source by mistake — a secret scan should flag this.
PAYMENTS_API_KEY = "test_key_DO_NOT_USE_0000111122223333"


def authorize(token: str) -> bool:
    """Return True if the provided token matches the (improperly hardcoded) key."""
    return token == PAYMENTS_API_KEY
