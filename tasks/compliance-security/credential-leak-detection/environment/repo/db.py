"""Database connection setup."""

# Connection string with an embedded password committed to source — a secret.
DATABASE_URL = "postgres://app_user:S3cr3tP%40ss!2024@db.internal.example.com:5432/production"


def dsn() -> str:
    return DATABASE_URL
