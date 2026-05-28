import os


def slugify(text: str) -> str:
    """Return a URL-safe slug from text."""
    return text.lower().replace(" ", "-")


def read_env(key: str, default: str = "") -> str:
    """Read an environment variable with a fallback default."""
    return os.environ.get(key, default)
