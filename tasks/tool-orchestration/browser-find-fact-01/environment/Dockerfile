FROM harbor-agents-rich:latest
WORKDIR /app

# No local web content: the target is a live external site
# (https://quotes.toscrape.com/js/), reached BY the harness's browser tool, which
# is wired to the shared headless Chromium on wiley (CDP, see openclaw.json
# `browser.cdpUrl` / hermes config `browser.cdp_url`). The trial container only
# needs network to reach that CDP endpoint (allow_internet=true); the page fetch
# happens browser-side. We just provide a clean /app for the answer file.
RUN mkdir -p /app
