# harbor-agents-prebaked
# ---
# Base image with openclaw + hermes pre-installed so per-trial setup is
# (close to) zero. Used as the FROM for our task environment Dockerfiles.
#
# Build:
#   docker build -t harbor-agents-prebaked:latest \
#       environments/agent-prebaked/
#
# Verify:
#   docker run --rm harbor-agents-prebaked:latest \
#       bash -lc 'openclaw --version && hermes version'

FROM python:3.12-slim

# System deps required by both agents (matches what each adapter's
# install() installs at runtime, deduped).
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git ripgrep xz-utils \
    && rm -rf /var/lib/apt/lists/*

# nvm + node 22 + openclaw
ENV NVM_DIR=/root/.nvm
RUN mkdir -p "$NVM_DIR" \
    && curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install 22 \
    && nvm use 22 \
    && nvm alias default 22 \
    && npm install -g openclaw@latest \
        --fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000

# Make openclaw findable without `nvm use 22` each time.
RUN . "$NVM_DIR/nvm.sh" \
    && ln -s "$(which openclaw)" /usr/local/bin/openclaw \
    && ln -s "$(which node)" /usr/local/bin/node \
    && ln -s "$(which npm)" /usr/local/bin/npm

# Hermes (NousResearch installer; lands in /root/.local/bin)
RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh \
        | bash -s -- --skip-setup
ENV PATH=/root/.local/bin:/usr/local/bin:$PATH

# Smoke check; fail the build if either binary is missing.
RUN openclaw --version && hermes version

# Default working directory for task content.
WORKDIR /app
