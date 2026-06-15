---
status: IMPLEMENTED
epic: E5
date: 2026-06-12
---

# Repo topology scrub — keep internal infrastructure out of the public repo

**Epic:** E5 — Infra / Ops hygiene
**Date:** 2026-06-12
**Status:** IMPLEMENTED + history rewritten & force-pushed 2026-06-15 (see the
"History rewrite" section at the end). NOTE: the commit SHAs cited below (`e8a1279`,
`773cebe`, …) predate the `git filter-repo` rewrite and no longer exist — they are
kept only as logical references.
**Origin / triggered-by:** while committing the alternate-model axis
(`2026-06-11-alt-model-axis.md`), the operator asked to confirm we aren't exposing
topographical data. The new files were scrubbed in commit `e8a1279`; this spec
covers the **pre-existing** leaks the audit surfaced across the rest of the repo.

## Outcome (2026-06-12, commit `773cebe`)

The executed scope was **much broader than the initial audit** below (which only
matched the run-host / dev-host / memory-host nicknames). A broadened sweep found a
second tier of host nicknames — the memory host (~174 refs), the production
memory-group names, the storage host, and the memory-host docker network — across
~70 files.

What shipped:
- **Removed from the repo** (live-infra artifacts that re-leak on every regen; kept
  local + gitignored): `infra/` (memory-stack docker-compose mirror + recall config)
  and `agent-status.html` (generator embeds real service URLs + container config).
- **Scrubbed** host nicknames → "run host / dev workstation / memory host / storage
  host / production memory groups"; `/home/<user>` → `<repo>` or repo-relative;
  Infisical UUID → placeholder. Across docs, comments, dashboard generator sources.
- **Path strategy = relative** (operator-confirmed via Harbor source: CWD-relative
  `iterdir` at `config.py:141`); all configs unified + validated (parse + resolve).
- **Renamed the memory-host SSH env var to `MEMORY_HOST_SSH`** (the old name
  embedded the host nickname).
- **`tools/check_topology.sh`** added (nickname/home gate); the pre-existing
  `.githooks/pre-commit` network gate now excludes the generated dashboards (they
  embed synthetic task-fixture IPs).
- Dashboards `roadmap.html` + `task-catalog.html` regenerated clean.

## History rewrite + publish (2026-06-15, force-pushed)

The working-tree scrub above only cleaned HEAD; the topology was still in the
PUBLIC GitHub history (already pushed). On operator instruction, all history was
rewritten and force-pushed.

- **Secrets pre-check (none real → no rotation):** the `sk-ant-…` hits were doc
  prefixes; `BEGIN RSA PRIVATE` is the `compliance-security/secret-scan-01` task
  fixture; `client_secret` was embedded skill-doc text; `configs/oracle-placeholder.env`
  holds only a non-`sk-or-` placeholder. Real keys were never committed (they live
  in Infisical).
- **Method:** `git filter-repo`, two passes (case-sensitive, then case-INSENSITIVE)
  over all 127 commits: removed `infra/` + `agent-status.html` from all history;
  replaced every host nickname / `/home/<user>` path / Infisical UUID in **blobs AND
  commit messages** with placeholders. The git author persona is preserved via a
  negative lookahead. Verified: HEAD tree byte-identical (no over-match), 0 topology
  tokens across all history (blobs + messages, case-insensitive), `check_topology` green.
- **Pushed** (`--force-with-lease`): `main` → `5d19809`,
  `remediation/core-eleven-2026-06-10` → `6a579a5` (scrub base + concurrent
  baton-pipeline prod-agent-eval commits, verified topology-clean).
- **Auth note:** the push MUST run from the **dev workstation** (where `gh` is
  authed) over the mount — the run host has no GitHub credentials. (Cost several
  failed attempts pushing from the run host.)
- **Backup:** full pre-rewrite bundle in the run host's home
  (`~/harbor-tasks-pre-rewrite.bundle`); restore via `git clone` from it.
- **Residual limit (not fixable by git):** GitHub keeps the OLD pre-rewrite commits
  reachable by SHA until its own GC. For true removal: ask GitHub Support to purge
  unreachable commits, or make the repo private. Exposure was topology only
  (usernames, host nicknames, a docker network name, the Shared Infisical project
  UUID) — no credentials.

## Problem

harbor-tasks is a **public** repo (the `d247004` "scrub: parameterize internal
endpoints" commit already moved memory-host URLs + Infisical coords into the
gitignored `configs/local.env` + placeholdered `configs/local.env.example`).
But an audit on 2026-06-12 (`git grep` over tracked files, excluding the gitignored
`local.env`) found residual internal-topology leaks:

| Category | Count | Where |
|---|---|---|
| Home-dir paths `/home/<user>/…` (reveals usernames + machine layout) | **24 files** | 16 `configs/*.yaml`, 6 `backlog/*.md`, `metrics/track_a_weighted.py`, generated `roadmap.html` |
| Infisical project/org UUID | **1 file** | `backlog/2026-06-02-browser-and-pin-findings.md` |
| Machine nicknames (run-host / dev-host) (prose) | **19 files** | `AGENTS.md`/`CLAUDE.md`, backlog docs, etc. |
| Internal hostnames (memory-host name, internal-DNS suffix) | 0 tracked | already clean (in gitignored `local.env` only) |
| Internal IPs (private `10.x` range) | 0 tracked | already clean |

Most of the config home-paths are **also stale/broken**: they point at the
pre-move `/home/<dev-host-user>/harbor-tasks/…` layout, which doesn't exist on the
current run host (`/home/<run-host-user>/…/harbor-tasks`). So scrubbing them doubles
as a correctness fix — several `configs/*.yaml` would fail path resolution as-is.

## Scope

**In (operator chose the FULL scrub, 2026-06-12):**
- All 24 home-dir-path leaks → portable, username-free references.
- The 1 Infisical UUID → placeholder (matching the `LAN-IP` redaction convention).
- The 19 machine-nickname mentions (run-host / dev-host) across `AGENTS.md` +
  backlog docs → generic operational terms ("the run host" / "the dev workstation",
  bare tokens → `<run-host>`/`<dev-host>`). Load-bearing literals (any runtime
  default) are flagged for review rather than blindly replaced.
- A CI/footgun grep gate (`tools/check_topology.sh`) so this can't silently regress.

## Design decisions

### D1 — Config dataset/jobs paths → `${REPO}`-relative
- Configs run via `tools/run_track_a.sh` (which sets `REPO` and `os.path.expandvars`
  on the YAML before Harbor reads it): use `${REPO}/tasks/<cat>` and
  `${REPO}/jobs`. Proven in `e8a1279` for `core-suite{,-claude}.yaml`.
- Configs run via `harbor run -c <yaml>` **directly** (no driver expansion — Harbor
  itself does NOT expandvars), e.g. `oracle-core.yaml`, `validate*.yaml`: use
  **repo-relative** `tasks/<cat>` (resolved from CWD = repo root) and document
  "run from the repo root", OR wrap them in a tiny `REPO=… envsubst` shim. Verify
  Harbor resolves relative dataset paths against CWD before committing (one oracle
  run is free).
- This fixes the stale `/home/<user>` paths at the same time.

### D2 — Backlog / metrics / roadmap
- Backlog `*.md`: home paths in prose/examples → `<repo>/…` or `${REPO}/…`. Includes
  THIS session's specs (`2026-06-10-core-eleven-remediation.md`,
  `2026-06-11-alt-model-axis.md`) — they cite run-host paths in run examples.
- `metrics/track_a_weighted.py`: replace any hardcoded `/home/<user>` default with a
  repo-relative / env-driven path.
- `roadmap.html` is **generated** by `tools/roadmap.py` — fix the generator (its
  source string), then regenerate (`python3 tools/roadmap.py`). Do not hand-edit the
  HTML.

### D3 — The Infisical UUID
- `backlog/2026-06-02-browser-and-pin-findings.md`: redact the project/org UUID to a
  placeholder (`<infisical-project-id>`). The real coords live only in
  `local.env` (gitignored).

### D4 — Regression gate
- Add a grep check (`tools/check_topology.sh` + FOOTGUNS entry + optional
  CI/pre-commit) that fails if any TRACKED file (excluding `configs/local.env`)
  matches the topology SHAPES — any `/home/<user>` path, the memory-host name, a
  an internal-DNS hostname, a private `10.x` IP, or an Infisical-UUID shape — modulo the
  intended placeholders. Prefer shape-based patterns so the gate script itself
  carries no sensitive literals. Mirrors the existing `FROM harbor-agents-rich`
  CI check pattern.

## Acceptance criteria

- [ ] `tools/check_topology.sh` exits clean — no `/home/<user>` paths, memory-host
  name, an internal-DNS host, private `10.x` IP, or Infisical-UUID shape in tracked files
  (modulo the intended placeholders).
- [ ] All scrubbed configs still resolve their datasets (a free oracle run on the
  core suite + one direct `harbor run -c` config stays green).
- [ ] `roadmap.html` regenerated from the fixed generator (no hand-edit).
- [ ] Regression grep gate added (FOOTGUNS + CI).
- [x] Operator decision on machine-nickname scope: FULL scrub (recorded above, 2026-06-12).

## Notes
- Hostnames/IPs are already clean in tracked files — the run-host IP / memory-host
  references used THIS session were only in ad-hoc `ssh`/smoke commands, never
  committed.
- Do this BEFORE any push of the `remediation/core-eleven-2026-06-10` branch — the
  topology is in local history but not yet exposed externally.
