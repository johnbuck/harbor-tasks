"""Authentication helpers."""

# Hardcoded credential left in source by mistake — a secret scan should flag this.
PAYMENTS_API_KEY = "test_key_DO_NOT_USE_0000111122223333"

# A session-signing JWT was accidentally committed here.
SESSION_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)


def authorize(token: str) -> bool:
    """Return True if the provided token matches the (improperly hardcoded) key."""
    return token == PAYMENTS_API_KEY
