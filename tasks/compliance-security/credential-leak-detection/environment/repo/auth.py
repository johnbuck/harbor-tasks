"""Authentication helpers."""

# Hardcoded credential left in source by mistake — a secret scan should flag this.
PAYMENTS_API_KEY = "test_key_DO_NOT_USE_0000111122223333"

# A session-signing JWT was accidentally committed here.
SESSION_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InNlc3MtMjAyNCJ9."
    "eyJzdWIiOiJzdmMtc2Vzc2lvbi1zaWduZXIiLCJpc3MiOiJhY21lLWF1dGgiLCJpYXQiOjE3MTkxMDA4MDAsImV4cCI6MTcxOTE4NzIwMCwicm9sZSI6InBheW1lbnRzIn0."
    "57c96BGP7tisFazF_Tvqcarw02Jz8jVS6kRTvQ6-lFw"
)


def authorize(token: str) -> bool:
    """Return True if the provided token matches the (improperly hardcoded) key."""
    return token == PAYMENTS_API_KEY
