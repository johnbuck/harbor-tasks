# backlog

Per-feature specifications for harbor-tasks. Conventions follow the
magellan pipeline's backlog (and the retired `rube` repo that preceded
this one).

## File naming

`YYYY-MM-DD-<slug>.md` — the date is when the spec was first written,
not when implementation lands. Slug is lowercase-hyphenated.

Larger multi-phase efforts may use a category prefix like
`C1-YYYY-MM-DD-<slug>.md` (magellan precedent: `C1-` denotes a campaign,
`C2-` a follow-on, etc.). Use sparingly.

## Status lifecycle

Each spec has a status badge in its frontmatter:

- **PROPOSED** — draft, awaiting design review.
- **APPROVED** — design ratified, implementation can start.
- **IN PROGRESS** — work in flight; spec is the source of truth.
- **IMPLEMENTED &lt;date&gt;** — shipped; the spec is now archaeology, not direction.
- **DEFERRED** — accepted in principle but deprioritized.
- **REJECTED** — explored, decided against. Body explains why.

Once a spec reaches IMPLEMENTED, move the file to `backlog/done/` (via
`git mv`, preserving history) and update the index below. The file keeps
its name and date — `done/` is purely a status distinction.

## Required sections

Every spec includes:

- A frontmatter block: Title, Date, Status, Origin / triggered-by
- **Problem** — what's wrong or missing today, with evidence
- **Scope** — what's in, what's deliberately out
- **Design decisions** — the choices made and why
- **Acceptance criteria** — how we'll know it's done

Optional but encouraged:

- **Revision history** — when iterated, capture what changed
- **Open questions** — anything unresolved
- **Follow-up tickets** — pointers to derivative specs

## Index

### Shipped — in `done/`

- [2026-05-27 harbor adoption](done/2026-05-27-harbor-adoption.md) — retire rube, fork Harbor as the substrate
- [2026-05-27 agent adapters](done/2026-05-27-agent-adapters.md) — pre-baked base image + NoInstall + OpenRouter subclasses
- [2026-05-27 cost + token tracking](done/2026-05-27-cost-and-token-tracking.md) — per-trial usage + live OpenRouter pricing
- [2026-05-27 deterministic provider routing](done/2026-05-27-deterministic-provider-routing.md) — pin OpenRouter upstream host

### Proposed / in progress

- [2026-05-27 task suite design](2026-05-27-task-suite-design.md) — 17 categories × 67 shapes, first-sweep selection (IN PROGRESS)
- [2026-05-27 context-management category](2026-05-27-context-management-category.md) — long-session behavior tests (DEFERRED)
