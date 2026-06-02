# Harbor viewer — Claude analysis on subscription auth + durable fork launch

**Epic:** E5 — Observability & reporting
**Status:** IMPLEMENTED 2026-06-02.
**Date:** 2026-06-02
**Origin / triggered-by:** operator clicked the "Generate Analysis" button in `harbor view`
and nothing happened.

## Problem

`harbor view` exposes a **"Generate Analysis"** button (and a job-level "Analyze"
dialog) that asks Claude to summarize a trial's trajectory. Clicking it did nothing.

Two independent issues:

1. **The auth gate.** The endpoint (`viewer/server.py` →
   `POST /api/jobs/{job}/trials/{trial}/summarize`) calls
   `harbor.analyze.analyzer.Analyzer` → `analyze/backend.py::query_agent()`, which
   **hard-required `ANTHROPIC_API_KEY` and raised `RuntimeError` before doing
   anything** (`backend.py:103`). The trial-summarize endpoint has no try/except, so
   that became a bare HTTP 500; the frontend surfaced it as a toast with a generic /
   empty description — i.e. a dead button. The viewer process had no `ANTHROPIC_API_KEY`
   in its environment, so the gate always fired. `cli/quality_checker/quality_checker.py:100`
   (the `harbor check` command) has the **identical** gate.

   The gate is artificial: the Claude Agent SDK that `backend.py` wraps already
   authenticates via the logged-in **`claude` CLI** it spawns (subscription / OAuth
   credentials) when no API key is set — so the analysis can run on a Claude Code
   subscription with no standalone `sk-ant-…` key. `backend.py` simply refused to try.
   (The separate **"Chat with Claude"** button on a *task definition* —
   `viewer/chat.py` → `ClaudeSDKClient` — never had this gate, which is why it already
   worked while "Generate Analysis" failed.)

2. **The runtime ran from an ephemeral checkout.** The live dashboard on :8089 was
   launched with `uv run --project /tmp/harbor …`. `/tmp/harbor` is a **separate**
   git checkout of **upstream** (`origin = harbor-framework/harbor`) sitting in
   scratch space, *not* the canonical fork at `/home/trumble/harbor`
   (`origin = johnbuck/harbor`) referenced in the harbor-tasks README. `/tmp` is
   wiped on reboot, so any fix applied only there is non-durable, and there is **no
   persistent launcher** — the viewer was started by an ad-hoc command, so a reboot
   reverts the repoint.

## Scope

In:
- Soften the `ANTHROPIC_API_KEY` gate in `analyze/backend.py` and the parallel one in
  `cli/quality_checker/quality_checker.py` to accept the logged-in `claude` CLI.
- Make the canonical fork (`/home/trumble/harbor`) the tree the live viewer runs from.
- A small persistent launcher so the fork-launch survives reboot (task #91 — proposed).

Out:
- Issuing / wiring a standalone Anthropic API key (the subscription path makes it
  unnecessary).
- Building the viewer SPA from source (the build toolchain — `bun` — isn't installed;
  see Design decisions).
- Adding try/except to the summarize endpoints (the gate no longer fires; endpoint
  error-shaping is a separate upstream nicety, deliberately not touched).
- Pushing the fork branch to `johnbuck/harbor` (operator's call — see Follow-ups).

## Design decisions

- **Soften, don't remove, the gate.** Keep a helpful early failure for the genuinely
  unauthenticated case, but only when *neither* path exists:
  ```python
  if not os.environ.get("ANTHROPIC_API_KEY") and shutil.which("claude") is None:
      raise RuntimeError("No Anthropic auth available. Either export ANTHROPIC_API_KEY=...,
                          or install and log in to the `claude` CLI ...")
  ```
  Applied identically to both `backend.py::query_agent()` (covers the analyze package's
  `analyze.py` + `check.py`) and `quality_checker.py::QualityChecker.check()`.

- **Patch both checkouts, but make the fork canonical.** Applied the patch to the live
  `/tmp/harbor` (fixes the button *now*) AND to the fork (durable), then repointed the
  running viewer at the fork via `uv run --project /home/trumble/harbor`. One source of
  truth going forward.

- **Reuse the prebuilt UI instead of building fresh.** `view.py` builds the SPA with
  `bun`, which isn't installed; only `node`/`npm` are. `/tmp/harbor`'s HEAD
  (`177b0c0`, 2026-05-26) is a confirmed **git ancestor** of the fork's HEAD
  (`8497620f`, 2026-05-27) — i.e. the fork is a strict superset one day newer — so the
  built frontend's API contract matches the fork's server. Copied
  `/tmp/harbor/src/harbor/viewer/static` into the fork (a build artifact; not committed)
  and launch with `--no-build`.

- **Branch, don't commit to fork `main`.** The patch lives on
  `local/subscription-auth-analyze` so the fork's `main` stays clean for tracking
  `upstream`. The editable install + the running viewer use whatever branch is checked
  out, so the branch *is* what runs.

## Acceptance criteria

- [x] `analyze/backend.py` + `quality_checker.py` accept subscription auth; both
      byte-compile.
- [x] Isolated proof: `query_llm("…", "haiku")` returns text with `ANTHROPIC_API_KEY`
      explicitly unset (`env -u`) — auth via the `claude` CLI subscription.
- [x] End-to-end: `POST …/summarize` returns **HTTP 200** with a real analysis (1925-char
      summary), served by the **fork** viewer; UI + `/assets/*` load 200.
- [x] Patch committed to the fork (`42e37e59` on `local/subscription-auth-analyze`);
      fork working tree clean apart from the untracked built `static/`.
- [x] Live :8089 viewer confirmed running from `/home/trumble/harbor/.venv` (the fork).
- [x] **Durable launcher** `tools/view.sh` pins `--project /home/trumble/harbor …
      --no-build` (port arg + `HARBOR_FORK`/`HARBOR_JOBS`/`HARBOR_HOST` overrides),
      preflights fork/UI/jobs/auth and waits out the TIME_WAIT restart race. Verified:
      launched the live viewer from the script → fork tree, UI 200, summarize 200.
      Task #91 — done.

## Follow-ups

- Optional: `git push -u origin local/subscription-auth-analyze` (or merge to the fork's
  `main`) to back the fork patch up off-disk — operator's call.
- `/tmp/harbor` still carries the same edits (harmless redundancy); it can be left to
  age out of `/tmp`.

## Revision history

- 2026-06-02 — auth patch implemented + verified end-to-end; fork made canonical and
  viewer repointed. Launcher carved out as task #91. Spec captured retroactively at
  operator request.
- 2026-06-02 (later) — task #91 done: `tools/view.sh` added and made the live launcher;
  all acceptance criteria met → status IMPLEMENTED. The only remaining item (optional
  off-disk push of the fork branch) is not an acceptance gate.
