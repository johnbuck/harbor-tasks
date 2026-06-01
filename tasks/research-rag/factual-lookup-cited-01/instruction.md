A company knowledge base — **Halcyon Systems** — is served locally at
`http://localhost:8780/`. Start at the landing page (`index.html`) and explore.

Answer the following **ten** factual questions about Halcyon Systems. For EACH
question you must provide both:

- the **correct current answer**, and
- a **source URL citation** that points to the **authoritative page** stating it
  (a URL like `http://localhost:8780/<path>`).

Write your answers to `/app/answer.md`, one numbered block per question, e.g.:

```
1. Answer: <value>
   Source: http://localhost:8780/<path>.html
```

## The catch: archived / near-duplicate pages

The knowledge base contains **current** pages AND **archived/legacy** pages that
look similar but state **outdated or superseded** values (an old press profile,
a 2018 team page, a legacy products page, an old changelog, a prior fiscal year,
an old contact page, an old regions page, a deprecated v1 API page). The landing
page marks which sections are current and which are archive/history.

You earn credit for a question **only when BOTH**:
1. the answer value is the **current/correct** one, AND
2. the cited source URL is the **authoritative page** for that fact — **not** an
   archived/legacy near-duplicate.

Citing an archived page (even if you happen to write the correct value) does **not**
earn credit. Each item is graded independently; partial credit is the fraction of
items you get fully right.

## Questions

1. In what **year was Halcyon Systems founded**?
2. Who is the **current CEO**?
3. In what **city is the company headquartered**?
4. What is the name of the company's **current flagship product**?
5. What is the **current GA version** of that flagship product?
6. **How many employees** does the company currently have?
7. What was the company's **annual revenue for the most recent fiscal year (FY2025)**?
8. What is the **current product-support email address**?
9. What is the **current primary production data-center region**?
10. What is the **free-tier API rate limit** (current API version), in requests per day?

## Tooling

- `fetch <path>` — GETs `http://localhost:8780/<path>` (e.g. `fetch about.html`).
- Or `curl http://localhost:8780/<path>` directly. No external network.
