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

- A frontmatter block: Title, **Epic**, Date, Status, Origin / triggered-by.
  `Epic:` names the roadmap epic the spec rolls up to (e.g. `E4 — Task Suite`) —
  the backlog stays a flat directory; epic membership is documented per-spec in
  frontmatter, not by folder. Epics are defined in `tools/roadmap.py` (→ `roadmap.html`).
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
- [2026-05-28 openclaw reasoning RESOLVED](done/2026-05-28-openclaw-reasoning-RESOLVED.md) — 4-part recipe to enable real reasoning over the OpenRouter passthrough
- [2026-05-28 pre-built rich harnesses (SHIPPED)](done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md) — the "stop using packaged harnesses" pivot; baked configs + thin adapters
- [2026-05-29 thin adapters](done/2026-05-29-thin-adapters.md) — `OpenClawThin` / `HermesThin`, one-key auth, persona staging, parity reproducer
- [2026-05-29 memory stack deployment](done/2026-05-29-memory-stack-deployment.md) — mem-embed + hindsight + honcho folded into the recall compose on wiley; recall allowlist fix
- [2026-05-29 hermes dual plugin system](done/2026-05-29-hermes-dual-plugin-system.md) — the System 1 / System 2 finding behind `hermes plugins list` being incomplete
- [2026-05-29 agent status dashboard](done/2026-05-29-agent-status-dashboard.md) — `tools/agent_status.py`; single-file HTML status board, dual-system aware
- [2026-05-29 recall bge-m3 + eval ontology (SHIPPED 2026-05-29)](done/2026-05-29-recall-bge-m3-and-eval-ontology.md) — recall migrated to bge-m3 + deepseek-v4-flash; community-build daily cron; parallel `recall-mcp-eval` container with coding-domain ontology
- [2026-05-29 recall hindsight-style plugin (SHIPPED 2026-05-30)](done/2026-05-29-recall-hindsight-style-plugin.md) — coaching descriptions + reflect + dispositions + directives + mental models; 4-phase build with adversarial reviews at design AND post-implementation, all findings folded back in (22 surfaced + 22 resolved including 9 deferred should-fixes resolved separately)

### Active (`backlog/`)

Status is each spec's frontmatter badge; the epic tag is its `Epic:` line.

- [2026-05-27 task suite design](2026-05-27-task-suite-design.md) — 17 categories × 67 shapes, first-sweep selection (IN PROGRESS · E4)
- [2026-05-27 context-management category](2026-05-27-context-management-category.md) — long-session behaviour: overflow + context-rot (IMPLEMENTED · E4)
- [2026-05-28 multi-step tasks](2026-05-28-multi-step-tasks.md) — Harbor `steps/` shape (IN PROGRESS · E4)
- [2026-05-28 tau3-bench integration](2026-05-28-tau3-bench-integration.md) — external multi-turn benchmark; **oracle shipped, agent-run DEPRECATED 2026-06-02** (E4)
- [2026-05-29 eval infra stack](2026-05-29-eval-infra-stack.md) — memory + browser BOTH shipped; browser (#90) closed 2026-06-03 via the stale-registry fix (E3)
- [2026-05-29 new eval tasks: subagent + research](2026-05-29-new-eval-tasks-subagent-research.md) — tasks #55, #56 (IMPLEMENTED · E4)
- [2026-05-30 harness-vs-model discriminating suite](2026-05-30-harness-vs-model-discriminating-suite.md) — rubric for what makes a task harness-discriminating; instrument proven interim (E4)
- [2026-05-30 goal-oriented real-world tasks](2026-05-30-goal-oriented-real-world-tasks.md) — `real-world-workflows` category; 11-mode failure taxonomy (PROPOSED · E4)
- [2026-05-31 discrimination-hardening session](2026-05-31-discrimination-hardening-session.md) — difficulty is the lever; graded scoring + crash penalty + catalog (E4)
- [2026-05-31 Task Suite page](2026-05-31-task-catalog-page.md) — `tools/task_catalog.py`; accordion + work-status + approval axes (IMPLEMENTED · E5)
- [2026-06-01 adversarial review](2026-06-01-adversarial-review.md) — only ~4 genuine discriminators; 23 deprecated (E4)
- [2026-06-01 methodology evidence base](2026-06-01-methodology-evidence-base.md) — approach grounded in published work (E4)
- [2026-06-01 telegraphing audit](2026-06-01-telegraphing-audit.md) — 37/50 leaked the trap; all fixed (E4)
- [2026-06-01 retired-task coverage matrix](2026-06-01-retired-task-coverage-matrix.md) — no capability left untested (E4)
- [2026-06-01 session status](2026-06-01-session-status.md) — pre-compact pickup log (not an epic spec)
- [2026-06-02 browser + provider-pin findings](2026-06-02-browser-and-pin-findings.md) — broken pin + openclaw browser not surfacing; the E2/E3 blockers (E3)
- [2026-06-02 roadmap page](2026-06-02-roadmap-page.md) — `tools/roadmap.py`; the by-epic plan view; the E4/E5 epic merge (IMPLEMENTED · E5)
- [2026-06-02 viewer subscription auth](2026-06-02-viewer-subscription-auth.md) — `harbor view` analyze button + `harbor check` on the `claude` CLI subscription; fork made canonical + `tools/view.sh` launcher (IMPLEMENTED · E5)
- [2026-06-02 context-rot scoring integrity](2026-06-02-context-rot-scoring-integrity.md) — false-zero audit grader (answer_present) + numeric-rewards schema fix + metric normalization (task #93: reward.json carries only normalized [0,1] keys; raw counts + answer audit moved to sibling reward-details.json) all shipped; only the #92-gated re-run remains (PARTIAL · E4)
- [2026-06-03 core suite selection](2026-06-03-core-suite-selection.md) — the 11 load-bearing harness-measuring tests (`configs/core-suite.yaml`), one per harness-distinct capability, anchored on the 3 proven discriminators; wired + validated, n=1 separation run pending; also records the recall-MCP removal from both harnesses (IMPLEMENTED · E4)
- [2026-06-03 RESULTS verdict thin over report](2026-06-03-results-verdict-thin-over-report.md) — retarget #81: numbers stay in Harbor reporting + `track_a_report.json` (auto-computed); RESULTS.md demoted to the thin verdict + caveats layer; FE exportable report deferred (APPROVED · E5)
- [2026-06-03 browser tool registry fix](2026-06-03-browser-tool-registry-fix.md) — the real #90 fix: stale baked plugin registry never indexed the `browser` plugin; bake `plugins registry --refresh` (46→64 enabled). Embedded `--local` then exposes the full 59-tool catalog (browser + memory) — proven identical to gateway-backed (IMPLEMENTED · E3)
- [2026-06-03 self-contained browser](2026-06-03-self-contained-browser.md) — bake `/usr/bin/chromium` + `start-cdp.sh` into the rich image; both harnesses' browser tools attach to an in-container `127.0.0.1:9222` instead of a shared Chromium on wiley. Verified e2e (both 1.0, 0 wiley refs) (IMPLEMENTED · E3)
- [2026-06-03 gateway-backed full-harness](2026-06-03-gateway-backed-full-harness.md) — REJECTED: the embedded-vs-gateway theory for #90 was disproven by experiment; the blocker was the stale registry (above), not embedded mode. Operator chose registry-refresh + keep embedded — no capability gap to close (REJECTED · E3)
- [2026-06-11 core-eleven second adversarial pass](2026-06-11-core-eleven-second-adversarial-pass.md) — 11 parallel auditors on the post-remediation core suite: 4 CRITICAL (2 demonstrated bypasses: 60/60 template parser on sub-agent-decompose, state forgery on failure-recovery) + 5 systemic patterns (`/app`-only wipe, format-strict false zeros, hedge gaming, no crash fallback, denominator drift); 4-wave fix plan + bypass-regression harness (APPROVED · E4)
