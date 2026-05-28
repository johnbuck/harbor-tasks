FROM harbor-agents-prebaked:latest

# rewardkit runs via uvx at verify time; provide uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
