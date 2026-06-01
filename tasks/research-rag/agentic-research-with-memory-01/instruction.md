A small research lab — **Mirador Labs** — has a public website hosted at `http://localhost:8780/`. Start at the landing page and explore from there.

Write a one-page brief about Mirador Labs and save it to `/app/brief.md`. The brief must cover all **eight** of these points, with each fact **cited to the page URL it came from** (citations in markdown link form: `[text](/path/page.html)`):

1. **The year the lab was founded.**
2. **The city where the lab is headquartered.**
3. **The name of the climate-modeling lead.**
4. **The lab's TOTAL NSF funding for 2025**, as a single dollar figure. Note: the lab has more than one 2025 NSF award (in different research areas) — add them up. Funding from *other* agencies (e.g. DOE) and NSF awards from *other years* do **not** count toward the 2025 NSF total.
5. **The total number of publications released in 2025** (the official published count, not draft/pipeline tallies).
6. **At least two named partner organizations.**
7. **The number of full-time staff in 2025.**
8. **The number of GPUs in the in-house training cluster.**

## Sources are not all equally trustworthy

The site includes a **press / media page** that reproduces a third-party article. That article contains several **plausible-but-wrong** figures (wrong founding year, wrong headquarters, wrong climate lead, wrong NSF total, wrong headcount, wrong GPU count, wrong publication count). The site itself says its own pages are authoritative and the press summary is not. **Cite each fact to the authoritative page that actually states it** — citing the press page (or any other page that merely repeats a figure non-authoritatively) for these facts will not earn credit.

Likewise, the publications section has an internal **draft/preprint tracker** with a larger pipeline tally; that is not the published count.

## Tooling available

- `fetch <path>` — convenience wrapper that GETs `http://localhost:8780/<path>`. Example: `fetch about.html`.
- Or use `curl http://localhost:8780/<path>` directly.
- No external network; only the local corpus.

## Format

The brief should be ~150-350 words, prose with citations, NOT a bulleted dump. Each cited fact should appear inline with its source URL.

Example shape:

> Mirador Labs is an open-research nonprofit [founded in 2024](/about.html) and based in [San Francisco](/about.html). The climate group is led by [Dr. Petra Holm](/people.html) ...

Don't fabricate facts, and don't repeat a figure from the press page as if it were correct. If a fact can't be found in an authoritative page, omit it.
