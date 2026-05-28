#!/bin/bash
# Reference solution.
set -e

pip install --no-cache-dir pydantic-settings==2.5.2

cat > /app/settings.py <<'EOF'
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    host: str = "localhost"
    port: int = 8080
EOF
