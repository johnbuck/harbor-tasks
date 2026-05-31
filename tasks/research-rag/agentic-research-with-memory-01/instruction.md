A small research lab — **Mirador Labs** — has a public website hosted at `http://localhost:8780/`. Start at the landing page and explore from there.

Write a one-page brief about Mirador Labs and save it to `/app/brief.md`. The brief must cover all five of these points, with each fact **cited to the page URL it came from** (citations in markdown link form: `[text](/path/page.html)`):

1. **When the lab was founded.**
2. **The total amount of NSF funding received in 2025** (a single dollar figure).
3. **The name of the climate-modeling lead.**
4. **The total number of publications in 2025.**
5. **At least two named partner organizations.**

## Tooling available

- `fetch <path>` — convenience wrapper that GETs `http://localhost:8780/<path>`. Example: `fetch about.html`.
- Or use `curl http://localhost:8780/<path>` directly.
- No external network; only the local corpus.

## Format

The brief should be ~150-300 words, prose with citations, NOT a bulleted dump. Each cited fact should appear inline with its source URL.

Example shape:

> Mirador Labs is an open-research nonprofit [founded in 2024](/about.html) and based in San Francisco. ... The climate group, led by [Dr. Petra Holm](/people.html), received [$X.X million in NSF funding in 2025](/research/climate.html) ...

Don't fabricate facts. If a fact can't be found in the corpus, omit it.
