#!/usr/bin/env python3
"""Generate roadmap.html — the plan + progress for the harbor-tasks harness-vs-model
eval, broken out by EPIC.

Sibling of tools/task_catalog.py (the TASKS) and tools/agent_status.py (the
HARNESSES). This page is the PLAN: the thesis, the epics, every backlog spec that
rolls up under each epic, its status, an expandable one-paragraph detail, and a
button that opens the ENTIRE backlog spec in a modal (content baked in at gen time,
so it works offline). Content is hand-curated — edit the EPICS table below and rerun:

    python3 tools/roadmap.py     # writes roadmap.html

Keep it clear and concise. Spec statuses mirror the backlog frontmatter badges.
Each spec row: (status, label, ref, detail). Rows display sorted by status —
in-progress first, deprecated/rejected last, everything else in between; the sort
is stable, so your curated list order holds within each bucket (see SORT_RANK).
  - ref  = backlog/ file (resolved against repo root and backlog/) or code file,
           or "—" for work with no standalone spec (tracked by task #). When the
           file exists, its full text is embedded and "open full spec" appears.
  - detail = the curated blurb shown when the row is expanded.
"""
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "roadmap.html"

THESIS = (
    "Evaluate performance between <b>Agentic harnesses</b>, independent of model."
)

# High-level, user-facing project status — ONE sentence, MAX.
# Keep it outcome-oriented: NO eval-internal mechanics, methodology, or
# agent-facing constraints belong here (those stay out of the public roadmap).
STATUS = (
    "The harness comparison runs end-to-end on one unified 33-task suite and has "
    "produced an initial head-to-head verdict; work now focuses on validating every "
    "task and making the scenarios realistic."
)

# status: done | partial | blocked | todo
EPICS = [
    {
        "id": "E1", "status": "done",
        "title": "Harness runtime & adapters",
        "summary": "Run both harnesses identically on Harbor — the foundation everything else sits on. Core path shipped; the one open runtime-install adapter was deprecated.",
        "specs": [
            ("done", "Harbor adoption — retire rube, build on Harbor", "done/2026-05-27-harbor-adoption.md",
             "Retired the bespoke `rube` runner and rebuilt on Harbor (Terminal-Bench / Terminus-2 lineage): tasks are task.toml + steps + a verifier; the oracle runs solve.sh with no LLM. Buys a maintained harness, schema validation, and a job dashboard."),
            ("done", "Agent adapters — pre-baked image + NoInstall + OpenRouter", "done/2026-05-27-agent-adapters.md",
             "Pre-baked base image so harness binaries aren't installed during each trial; NoInstall adapter subclasses invoke them; an OpenRouter subclass routes both harnesses' LLM calls through one API with per-call cost capture."),
            ("done", "Thin adapters — invoke the BAKED harness, no config rewrite", "done/2026-05-29-thin-adapters.md",
             "lib/openclaw_thin.py / hermes_thin.py run each harness against its BAKED config (`openclaw agent --local --json`). Key consequence: Harbor-injected mcp_servers are IGNORED — capabilities must be enabled in the baked image, not the task config."),
            ("done", "Pre-built rich harness images (configs + skills + tools)", "done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md",
             "harbor-agents-rich:latest bakes the full configs + skills + tooling (jupyter/debugpy) so a trial boots a realistic agent, not a bare CLI. This is the image every task's Dockerfile must FROM."),
            ("done", "openclaw reasoning on OpenRouter — resolved", "done/2026-05-28-openclaw-reasoning-RESOLVED.md",
             "openclaw initially emitted no reasoning over OpenRouter; resolved and verified end-to-end (QuixBugs) so both harnesses genuinely reason on the shared model — a precondition for a fair comparison."),
        ],
    },
    {
        "id": "E2", "status": "done",
        "title": "Fair-comparison controls",
        "summary": "Same model, same provider, isolated state — so a score gap is the harness, not luck.",
        "specs": [
            ("done", "Deterministic provider pin — one shared OpenRouter host (novita)",
             "done/2026-05-27-deterministic-provider-routing.md",
             "Both harnesses must hit ONE OpenRouter upstream or cost/cache differ run-to-run. The pin had regressed to `only:[deepseek]` which, once DeepSeek's deepseek-v4-pro endpoint became training-flagged, left 0 endpoints under data_collection:deny → 404 on every hermes call. RESOLVED 2026-06-03: re-pinned both harnesses to **novita** (byte-identical provider.only in openclaw.json + hermes config.yaml). Fireworks was deny-eligible but lacks tool-use for this model; novita serves deepseek-v4-pro under deny + tool-use + reasoning + require_parameters (all verified via direct API probes + a live oracle/openclaw/hermes probe — all three reward 1.0). data_collection:deny preserved (privacy intact)."),
            ("done", "Cost + token tracking — per-trial usage at live pricing", "done/2026-05-27-cost-and-token-tracking.md",
             "Per-trial token + dollar cost from live OpenRouter pricing, including cache-write tokens. This is what surfaces the efficiency signal — openclaw spends ~0.35–0.62× hermes's cost for equal results on the same model."),
            ("done", "Memory-state wipe hook — reset harness memory at trial start", "hooks/wipe_memory_state.py",
             "Wipes the harness memory backend at TrialEvent.START so a memory task must re-derive state THROUGH the harness, not inherit it from a prior trial. Scoped to eval groups only."),
        ],
    },
    {
        "id": "E3", "status": "done",
        "title": "Capability infrastructure (memory + browser)",
        "summary": "The subsystems the harnesses actually use — memory + a shared browser. Both halves shipped: memory stack on the memory host, and the browser tool unblocked (stale-registry fix) + verified driving the shared Chromium end-to-end on BOTH harnesses.",
        "specs": [
            ("done", "Eval memory stack — the memory host deployment, LAN-reachable", "done/2026-05-29-memory-stack-deployment.md",
             "Recall / Graphiti memory services deployed on the memory host and reachable from the eval network (8408/8888) so trials can exercise the harnesses' long-term memory."),
            ("done", "Recall — bge-m3 embedder + extractor + community-build", "done/2026-05-29-recall-bge-m3-and-eval-ontology.md",
             "Re-embedded prod groups with bge-m3 + a deepseek-v4-flash extractor and scheduled community detection — the memory substrate both harnesses read and write against."),
            ("done", "Recall — hindsight-style tool surface (P1–P4)", "done/2026-05-29-recall-hindsight-style-plugin.md",
             "Four phases: coaching tool descriptions, a reflect tool, bank config + directives, and mental-models + a refresher cron with row-locking — the surface the agent uses to store and recall facts."),
            ("done", "Hermes dual-plugin activation", "done/2026-05-29-hermes-dual-plugin-system.md",
             "Investigated and activated hermes's two independent plugin systems so it exposes the same capability classes openclaw does."),
            ("done", "Eval infra stack — memory + browser both shipped", "2026-05-29-eval-infra-stack.md",
             "The combined memory + browser infra spec. Memory half shipped earlier; the browser half closed 2026-06-03 (stale-registry fix below, verified e2e on both harnesses)."),
            ("done", "Browser tool enablement — stale plugin registry (task #90)", "2026-06-03-browser-tool-registry-fix.md",
             "Both harnesses wired to a shared headless Chromium on the memory host (CDP :9222). 2026-06-03 REAL ROOT CAUSE (supersedes BOTH the CDP-reachability guess AND the embedded-vs-gateway theory): the rich image shipped a STALE persisted plugin registry (/root/.openclaw/plugins) indexed before the `browser` plugin's deps were present, so browser (+ canvas/file-transfer/phone-control/talk-voice) were never indexed and their tools never surfaced — embedded OR gateway-backed. Fix is one line baked into the image: `openclaw plugins registry --refresh` (46 → 64 enabled). Proven in-container: after refresh, plain embedded `openclaw agent --local` exposes the identical 59-tool catalog as gateway-backed (browser + full hindsight memory + sessions_spawn/subagents + 14 skills). Embedded is NOT a reduced runtime for anything the suite exercises — so the prior 'must go gateway-backed' conclusion was wrong (see the row below)."),
            ("done", "Self-contained in-container browser (no cross-machine CDP)", "2026-06-03-self-contained-browser.md",
             "The browser tool drove a shared Chromium on <MEMORY-HOST> (CDP :9222) over the LAN — a cross-machine dependency that violated the self-contained requirement (and accidentally disabled each harness's own local browser). Fixed: bake a real `/usr/bin/chromium` (148) into the rich image + `/etc/chromium.d` no-sandbox flags (run-as-root) + an idempotent `start-cdp.sh` that launches a headless Chromium INSIDE each trial container; both harnesses' browser tools attach to `127.0.0.1:9222`. One controlled browser backend per container keeps the comparison fair (only the harness's tool differs). Verified e2e: openclaw 1.0 / 13 calls, hermes 1.0 / 60 calls, trajectory shows `127.0.0.1` and ZERO <memory-host> refs (prior run had 18). Memory (hindsight :8888) is still the shared <memory-host> substrate by design — separate decision."),
            ("rejected", "Gateway-backed full-harness execution — NOT NEEDED (was the #90 theory)", "2026-06-03-gateway-backed-full-harness.md",
             "Spec written on a premise that the experiments disproved. The theory: thin `--local` runs EMBEDDED, dropping the gateway's browser control server → no browser tool. Reality: the blocker was the stale plugin registry (row above); once refreshed, embedded `--local` exposes browser + memory + the full 59-tool catalog identically to gateway-backed. The gateway adds only channels/cron/device-pairing/multi-session-routing/sidecars — none of which the eval tasks touch. Operator decision (2026-06-03): ship the registry-refresh fix, KEEP the embedded `--local` invocation (simpler, no gateway lifecycle / port-collision / teardown risk, and proven fair). Gateway-backed left as rejected, not deferred — there is no capability gap to close."),
        ],
    },
    {
        "id": "E4", "status": "partial",
        "title": "Task Suite",
        "summary": "Build the tests AND prove they measure the harness, not the model — authoring and validity are one feedback loop, so they're one epic. Author a task, review it, and if it's blunt it routes straight back to re-authoring; the goal is one unified suite (33 tasks) that genuinely separates the harnesses, ending in the verdict grid.",
        "specs": [
            # ── authoring: the categories, shapes, and task instances ──
            ("partial", "Task suite design — categories, shapes, first-sweep selection", "2026-05-27-task-suite-design.md",
             "The taxonomy: ~10 categories × shapes and which subset runs in the first sweep. A living document as shapes are added, sharpened, or retired."),
            ("done", "Context-management category — long-session behaviour", "2026-05-27-context-management-category.md",
             "How the agent behaves as its context window fills — eviction, update-churn, cross-talk — sized to overflow the operative window so the harness has to compact/externalise. Promoted out of DEFERRED 2026-05-30."),
            ("done", "Multi-step task suite — design + specs", "2026-05-28-multi-step-tasks.md",
             "DONE — multi-step is the suite's backbone: 12 of the 33 tasks use Harbor's steps/ layout (per-step setup.sh wipes scratch so state must survive via the harness, not the filesystem), incl. the 19-step context tasks. All 4 specced shapes shipped (scaffold-implement-document since archived); every open item is closed — openclaw reasoning-passthrough RESOLVED, the multi-step sweep folded into the unified suite, tau3-bench dropped as out of scope."),
            ("done", "Sub-agent spawning + research tasks", "2026-05-29-new-eval-tasks-subagent-research.md",
             "Two shapes shipped 2026-05-30: a sub-agent fan-out task (N non-batchable prose problems so parallel delegation beats serial, reward = fraction solved) and a research task."),
            ("done", "Goal-oriented real-world workflows", "2026-05-30-goal-oriented-real-world-tasks.md",
             "Workflows modelled on how users actually drive agents. All 3 shapes shipped + oracle-validated + hardened. update-record-with-cleanup-01 is the stateful-workflow discriminator (/16 — it carried the n=5 grid); schedule-meeting-from-name-01 + prompt-injection-resistance-01 are also in the suite — prompt-injection measures model-level safety, not the harness (so it isn't expected to discriminate), and schedule-meeting needs a sidecar redesign. Category built + scoring."),
            ("rejected", "tau3-bench — REMOVED from scope (not part of the comparison)", "2026-05-28-tau3-bench-integration.md",
             "Decided long ago: tau3 (an external benchmark) is NOT part of this harness-vs-harness eval and produces no comparison data. The thin adapter can't forward Harbor's injected tau3 MCP, and building an install-during-trial adapter wasn't worth it for one external benchmark. Out of scope — kept only as an inert reference; nothing downstream depends on it."),
            # ── discrimination & validity: do the authored tasks actually measure the harness? ──
            ("done", "Harness-vs-model discriminating suite — instrument PROVEN at n=5", "2026-05-30-harness-vs-model-discriminating-suite.md",
             "The central spec: evaluate the SCAFFOLDING, not the LLM. The interim caveat is now discharged — a full n=5 pass^k grid (110 trials) ran on the symmetric hindsight-only substrate and the suite DISCRIMINATES: effective Δ=0.188 (meets the 10% bar), leader hermes, all 7 categories split ≥10% in BOTH directions (hermes 5, openclaw 2). Reliability is the signal — hermes 4% error vs openclaw 20%. See the n≥3 verdict-grid row below + RESULTS.md."),
            ("done", "Methodology evidence base — approach grounded in published work", "2026-06-01-methodology-evidence-base.md",
             "Five sourced research passes grounding each claim: harness≠model (Terminal-Bench / Aider / METR), pass^k as the reliability metric (τ-bench), telegraphing as a construct-validity threat, context-overflow caveats (effective window ≪ 1M), and provider-pin necessity."),
            ("done", "Discrimination-hardening sweep — difficulty is the lever", "2026-05-31-discrimination-hardening-session.md",
             "Found that DIFFICULTY (not rubrics) manufactures a split — binary tasks saturate to 1.0 for two competent harnesses. Added graded scoring, a crash/timeout penalty in the analyzer, and the task-catalog page."),
            ("done", "Adversarial review — only ~4 genuine discriminators found", "2026-06-01-adversarial-review.md",
             "A 6-agent aggressive review of all 50 tasks: only ~4 genuine harness discriminators; ~23 model-dominated one-shots; a few outright broken. The KILL test: if `python3 -c` or one file-read solves it, you're measuring the MODEL. 23 deprecated non-destructively."),
            ("done", "Telegraphing audit — 37/50 leaked the trap; all fixed", "2026-06-01-telegraphing-audit.md",
             "37 of 50 tasks told the agent the very strategy the verifier secretly measured (\"the latest value supersedes earlier ones\"), so they tested instruction-following, not the latent capability. All fixed across 7 waves; load-bearing constraints now enforced mechanically."),
            ("done", "Retired-task coverage matrix — no capability left untested", "2026-06-01-retired-task-coverage-matrix.md",
             "Mapped every deprecated task to the capability axis it covered, so retiring the KILL set leaves no axis silently untested."),
            ("rejected", "Rework the 20 salvageable deprecated tasks (task #89) — DROPPED, superseded", "2026-06-01-retired-task-coverage-matrix.md",
             "DROPPED 2026-06-23. Audited: 20 (not 22) tasks are deprecated-on-disk (task.toml status=\"deprecated\"), auto-excluded by the sweep driver — they feed NO live config and are never scored. Per the retired-task coverage matrix every capability axis they covered is already exercised by a HARDER live task (memory→memory-conversational, sub-agent→parallel-decompose, tool-orch→tool-sprawl, etc.), so reworking them adds redundancy, not coverage. The label had drifted: #89 was originally 'rework the live cover tasks' — that work shipped as the suite-remediation pass. The genuine remaining rework is the other 21 active tasks (row below), not the dead ones. Deprecated tasks stay dormant on disk as a non-destructive audit trail."),
            ("partial", "Task remediation — 21 active tasks HARDENed (validation pending)", "2026-06-16-noncore-task-remediation.md",
             "The real remaining E4 rework (replaces the mislabelled #89). IMPLEMENTED + offline-green 2026-06-17, merged into this branch via baton (as-built in the spec) — NOT a build-in-progress. Wave 0 triage (21/21) found all 21 already emit graded reward.json, so the work was validity/discrimination hardening, not binary→graded conversion. Shipped: universal S4 crash-fallback + answer_present on all 21; the 6 CRITICAL grader fixes + tool-selection honest-channel, each with an exploit-regression test; WIPE_PRESERVE_SESSIONS for in-window retention; Wave-3 de-telegraphing + format-robustness; Wave-4 docs/hygiene — all backed by a full offline pytest suite (exploit/regrade/S4/wipe/hygiene) that passes. REMAINING = OPERATOR gates only (explicitly out of the no-Docker pipeline): Docker oracle=1.0 + n≥3 runs, then flip approved=true per task (0 flipped by design — a guard test enforces it, so the catalog still reads NEEDS REVIEW), plus the corpus-balloon / keep-vs-demote call for find-contradictions-01 + factual-lookup-cited-01 and the browser_used matcher validation. Additive validity work — outside the first verdict grid."),
            ("done", "Context-rot scoring integrity — false-zero audit + metric normalization", "2026-06-02-context-rot-scoring-integrity.md",
             "A hermes context-rot-02 trial scored 0 after recalling all 8 chains correctly — its staged write never landed in /app, so the verifier read an empty file (a false zero that faked a 0.875-vs-0 gap; hermes actually beat openclaw 8/8 vs 7/8). SHIPPED: recall graders now archive answer.md + emit numeric answer_present (0 = VOID, not wrong); reward.json kept dict[str,float|int] (a string field silently drops the trial from the viewer). Recorded result hand-corrected (stopgap; real fix = re-run via task #92). SHIPPED (task #93): reward.json now carries ONLY normalized [0,1] keys with identical names on both tasks — reward, correctness, and early/middle/late as per-depth fractions (so the rot curve compares across rot-01's 4/bucket and rot-02's 2-3/bucket). Raw counts (facts/chains) + the answer audit (answer_present/answer_chars) moved to a sibling reward-details.json that Harbor never aggregates — killing the cross-task blend (chains=(0+8)/2=4.0, answer_chars 85→42.5 masquerading as a score). All three scoring-integrity deliverables shipped; the lone residual — re-running existing trials under the new keys — is owned by #92 (write-persistence) + the #81 verdict grid, not this work."),
            ("done", "The 11 load-bearing harness-measuring tasks (now part of the unified suite)", "2026-06-03-core-suite-selection.md",
             "Selected 11 load-bearing tasks, one per harness-distinct capability, anchored on the three PROVEN discriminators (memory-conversational-01 Δ0.50, failure-recovery-loop-01 1.0-vs-0.0, tool-sprawl-precision-01 efficiency 3-vs-7 calls). Same model both harnesses ⇒ any gap is the harness. Coverage: memory ×3 (recall-under-load / proactive-write+correction / stale-vs-live-file), long-context ×2 (compaction-on-overflow / in-window rot), control-loop ×2 (recovery+retry / mid-task replan), tool-precision ×1 (selection among 57 decoys, F1), delegation+skill ×2 (sub-agent fan-out / skill discovery), stateful workflow ×1 (ledger edit w/ preservation traps). Left prompt-injection (model-level safety, not harness) + the wt-0.5 model-dominated families out of this initial discriminator set; top alternates (find-contradictions, factual-lookup-cited) named for swap-in if a task fails to separate. SUPERSEDED 2026-06-25: the old curated-subset split is retired — all 33 tasks are one unified suite (see the unify spec), and discrimination is a per-task outcome at n≥3, not a tier. Wired as configs/suite.yaml + structurally validated (all 11 paths/graders resolve; runner honors CONFIG/N_ATTEMPTS/JOB_NAME). n=1 separation run pending the image rebuild."),
            ("done", "Recall MCP dropped from both eval harnesses — memory substrate change", "2026-06-03-core-suite-selection.md",
             "recall (Graphiti temporal-KG memory, <memory-host>:8408) was erroring on every hermes invocation, so it was removed from BOTH harness configs (openclaw.json mcp.servers + hermes config.yaml mcp_servers) to keep the comparison fair and unblocked — hindsight kept in both, hermes honcho untouched, and the memory host recall server itself left intact (the harnesses just no longer mount it). New substrate: openclaw=hindsight vs hermes=honcho+hindsight. Consequence: the old Δ0.50 memory-conversational-01 baseline is VOID (measured on the recall-bearing substrate) — RESULTS.md 'Known asymmetries' + the proven-discriminator note both corrected. Takes effect after a harbor-agents-rich rebuild. Commits 597070b + 8f812e1."),
            ("done", "Hermes write-persistence (#92) — false-zero root cause fixed", "2026-06-02-context-rot-scoring-integrity.md",
             "The context-rot-02 false-zero: hermes's write_file reported 85 bytes but /app/answer.md was empty at verify. Root cause = hermes's file tools are workspace-rooted at the terminal backend's cwd (`terminal.cwd: \".\"`); the adapter never cd'd to the task workdir, so writes landed in a cwd-shadow the verifier (reading /app) never saw — while openclaw's direct write landed. Fix (lib/hermes_thin.py, commit e1c4541): `cd /app && hermes …`. Verified via the file-persistence-01 probe (tasks/_verify): hermes answer_present 0→1, reward 1.0, alongside openclaw 1.0 + oracle 1.0. The probe is a reusable write-persistence regression."),
            ("done", "Verifier-integrity audit — all 54 tasks; 2 proven discriminators GAMEABLE", "2026-06-09-verifier-integrity-audit.md",
             "7-agent audit of every task's grader for forge surface. HEADLINE: two of the three proven discriminators can be FAKED — failure-recovery-loop-01 (success string baked in an agent-readable script + plantable payload.txt → full reward without the recovery path) and tool-sprawl-precision-01 (tool_f1 read from a chmod-666 log the agent can append to). 11 live gameable tasks (Wave 1), ~21 rewardkit-only modernization, ~21 leave-as-is (code-editing already /opt/canonical tamper-guarded). A gameable discriminator silently invalidates the thesis — validity-critical."),
            ("done", "rewardkit grading rollout — all 23 active graded tasks converted + validated", "2026-06-09-verifier-sandbox-rollout.md",
             "Operator directive: rewardkit is the grading framework — RE-IMPLEMENT bespoke bash/python graders cleanly in it (most of FOOTGUNS is bespoke-grader bugs), keep bespoke only for pytest tasks. rewardkit BAKED into harbor-agents-rich:latest (+ canonical Dockerfile) so shared-mode conversion = just reward.py + test.sh + oracle --force-build. ALL 23 active graded tasks DONE + oracle-validated (verified criterion counts, $0 OpenRouter) across patterns: additive, penalty max(0,found-fp)/N (weight-1 score + weight-0 detail), F1-blend, binary, blend, net-penalty UPDATE-trap, line-anchored cross-talk, and positional lost-in-the-middle recall. 12 single-step + 11 multistep (the recall-step reward.py grades; multi_step_reward_strategy=final). #93 context-rot rot-curve fractions + answer_present preserved as weight-0 criteria. Footguns found: zero-arg criteria double-register (#45); vestigial verifier.env breaks grading. Only the 4 pytest tasks stay bespoke (by design). Separate-verifier sandbox (environment_mode=separate, FOOTGUNS #42) used where isolation is needed; isolation alone doesn't fix a forged artifact (#44). 5 commits local on the run host main pending operator push."),
            ("done", "Overnight verifier-integrity decisions — honest-shortcut fixes + NORTH_STAR.md", "2026-06-10-overnight-verifier-integrity-decisions.md",
             "Threat-model refinement (2026-06-10): this eval measures HONEST harnesses, so the priority is closing honest-shortcut leaks (a capable agent legitimately reading a baked answer — a KILL-test fail) over adversarial-forge hardening (fabricating a log honest harnesses never touch). DONE + oracle-validated on the free oracle ($0 OpenRouter): unit-tests-01 (the 4 grading mutants relocated environment/→tests/ so Harbor uploads them only AFTER the agent runs — answer-key leak closed) and the proven discriminator failure-recovery-loop-01 (the plaintext `PAYLOAD: …` literal in the agent-readable dfetch script → DERIVED from the session token, sha256(token)[:11], at emit time; the task now passes the KILL test on the identical 2-call honest path, so discrimination is unchanged — only the emitted/expected string moved in lockstep). Adversarial-forge tasks (tool-sprawl / tool-selection / browser-find-fact / prompt-injection) deprioritized as speculative for an honest-harness verdict; schedule-meeting-from-name-01 deferred (its fix isn't safe to do unsupervised). New: NORTH_STAR.md — the canonical value hierarchy (validity > measure-the-harness > no-telegraphing > pass^k > fair-comparison > simplicity) for unsupervised judgment calls. Feeds the n≥3 verdict grid (#81) below — failure-recovery's supervised re-baseline is incorporated there."),
            ("done", "Run n≥3 pass^k grid → verdict (task #81) — first grid DONE", "2026-06-10-core-eleven-remediation.md",
             "DONE 2026-06-10: a full n=5 pass^k grid (110 trials) ran on the 11 remediated discriminator tasks over the symmetric hindsight-only substrate, after all 5 known bypasses were closed and re-verified live (a second agent re-ran each exploit — 5/5 no longer score). Result: effective Δ=0.188 (meets the 10% bar), leader hermes, all 7 categories split ≥10% in both directions — the three reworked anchors RE-EARNED real splits (ops-debugging Δ+0.33, tool-orchestration Δ+0.15, conversation-persona Δ−0.53). Numbers auto-computed by metrics/suite_weighted.py → suite_report.json; verdict written to RESULTS.md (E5). Open follow-on: extend the grid to the other 21 active tasks (their hardening has landed — row above; the operator-gated oracle + n-runs are what's pending); re-confirm context-rot (Δ−0.10, thin)."),
            # ── 2026-06-25 unification + legibility/validity hardening ──
            ("done", "Unify the full suite — one suite, one validation bar", "2026-06-25-unify-full-suite.md",
             "IMPLEMENTED 2026-06-25 (commit 7be4767). Retired the old privileged-subset split and the dual-track framing: there is now ONE suite of 33 equally-important tasks under ONE bar. Configs/driver/metrics/tests/docs were de-tiered + renamed to neutral 'suite' names (the sweep config, the run driver, the weighted aggregator); a guard test fails if the retired vocabulary reappears in live source. Whether a task separates the harnesses is now a per-task OUTCOME measured at n≥3, not a pre-assigned tier. the offline test suite stayed green throughout (the pre-existing tests preserved + a new framing-guard)."),
            ("done", "Human-readable task names + per-task 'how it works'", "2026-06-25-unify-full-suite.md",
             "All 33 active tasks renamed from <shape>-NN ids to descriptive names (commit 7550dfa) so a reviewer grasps each task from its name (distinguish-my-facts-from-others, adaptive-tool-error-recovery, clean-expense-ledger). The Task Suite dashboard now carries a one-line plain-language 'how it works' per task."),
            ("done", "Both-zero grader/fixture fixes (n=1 smoke false-zeros)", "2026-06-25-both-zero-grader-fixes.md",
             "Two tasks scored 0 on BOTH harnesses in the n=1 smoke purely from a grader bug / bad fixtures, not real failure. FIXED + regression-tested: persist-facts-through-corrections (Part-A/B splitter anchored to a heading; meat-token regex word-boundaried) and credential-leak-detection (fixtures reseeded off canonical example secrets)."),
            ("done", "100% rewardkit grading — the standard, now met", "2026-06-25-rewardkit-100pct-grader-conversion.md",
             "Operator standard (2026-06-25): EVERY active task grades via rewardkit, no exceptions (pytest wrapped). The hard rule + tools/check_rewardkit.py CI gate landed first (ba454c7); the remaining graders were then converted (commit f5028a9) — all 33 tasks are now rewardkit-compliant and the gate passes. (Spec frontmatter still reads PROPOSED pending its as-built flip.)"),
            ("todo", "Rebuild task CONTENT into believable scenarios", "2026-06-25-task-content-rebuild-scenarios.md",
             "The suite is legible by NAME; several tasks' CONTENT is still synthetic filler (PROJECT VEGA, 60 opaquely-named tools, WESTMARCH PRIORY). Rebuild into scenarios a real user would plausibly hand an agent WITHOUT losing each task's power to separate the harnesses. PROPOSED — one task per run, oracle-gated."),
        ],
    },
    {
        "id": "E5", "status": "partial",
        "title": "Observability & reporting",
        "summary": "See the state at a glance, and publish the verdict.",
        "specs": [
            ("done", "Agent-status dashboard — the two harnesses", "done/2026-05-29-agent-status-dashboard.md",
             "tools/agent_status.py renders each harness's config/state/parity at a glance — the HARNESS view."),
            ("done", "Task Suite page — review + work tracker for every task", "2026-05-31-task-catalog-page.md",
             "tools/task_catalog.py → task-catalog.html (titled “Task Suite”). Drift-proof accordion over every task: what it asks, how it's graded, the oracle, the environment — plus a per-task WORK status (discriminating / needs-validation / needs-hardening / retired) and an OPERATOR-APPROVAL axis (every task is NEEDS REVIEW until its task.toml sets approved=true). Regenerates from the on-disk tree."),
            ("done", "Roadmap page — this page (epics + status)", "2026-06-02-roadmap-page.md",
             "tools/roadmap.py → roadmap.html — the PLAN view: the thesis, a where-we-stand callout, the epics, every backlog spec rolled up under one with a status dot, an expandable detail, and an open-full-spec modal. Hand-curated EPICS table; re-run after backlog changes."),
            ("done", "Viewer Claude-analysis on subscription auth + durable fork launch", "2026-06-02-viewer-subscription-auth.md",
             "The “Generate Analysis” button in `harbor view` 500'd: the analyze/summarize backend (and `harbor check`) hard-required ANTHROPIC_API_KEY and raised before trying — but the Claude Agent SDK already authenticates via the logged-in `claude` CLI it spawns, so analysis runs on a subscription with no API key. Softened both gates; committed to the fork (local/subscription-auth-analyze) and repointed the viewer off the ephemeral /tmp checkout onto the fork. `tools/view.sh` pins the fork launch so it survives reboot. Verified end-to-end: UI 200, summarize 200 via subscription auth."),
            ("done", "RESULTS.md — thin verdict over the auto-computed report (task #81)", "2026-06-03-results-verdict-thin-over-report.md",
             "WRITTEN 2026-06-10 once the first suite grid ran. RESULTS.md is the THIN layer no automated report can produce: the plain-English verdict (the suite discriminates, effective Δ=0.188, leader hermes, driven by reliability — hermes 4% vs openclaw 20% error), the construct-validity caveats (honcho asymmetry, recall-removed, n=1-is-a-coin-toss, false-zero/VOID traps), and the reproduction command — embedding the auto-computed split block, never a hand-typed table; numbers stay owned by metrics/suite_weighted.py → suite_report.json. Will refresh when the full-suite grid lands."),
            ("todo", "FE exportable verdict report (follow-up)", "2026-06-03-results-verdict-thin-over-report.md",
             "Extend the front-end (viewer / dashboards) to EMIT an exportable verdict file — a 'Download report' that bundles the split + pass^k + caveats into a standalone artifact, so the verdict isn't a manual paste. When it ships, RESULTS.md becomes the export target (or is generated by it). Deferred until after the first verdict run."),
        ],
    },
]

STATUS_LABEL = {"done": "done", "partial": "in progress", "blocked": "blocked",
                "todo": "to do", "deprecated": "deprecated", "rejected": "rejected"}
STATUS_CLASS = {"done": "ok", "partial": "mid", "blocked": "bad",
                "todo": "muted", "deprecated": "dep", "rejected": "dep"}
# Display order within an epic: in-progress first, dead (deprecated/rejected) last,
# everything else (done/blocked/todo) in between. Stable sort, so the curated list
# order holds within each bucket.
SORT_RANK = {"partial": 0, "deprecated": 2, "rejected": 2}

CSS = """
  body{font:14px/1.6 system-ui,sans-serif;margin:0;background:#0f1117;color:#e6e6e6;padding:24px}
  a{color:#9db4d6}
  .nav{display:flex;gap:10px;align-items:center;margin-bottom:14px}
  .nav a{font-size:13px;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:4px 12px;color:#9db4d6}
  .nav a:hover{background:#1c2331}
  .nav a.active{background:#1b2a1f;border-color:#3a5a44;color:#9fe0a5;font-weight:600}
  h1{font-size:18px;margin:0 0 2px} .ts{color:#8a8f98;font-size:12px;margin-bottom:18px}
  .wrap{max-width:1000px}
  .mono{font-family:ui-monospace,Menlo,monospace}
  .thesis{background:#13182098;border:1px solid #2a3550;border-left:3px solid #5fd0d0;border-radius:10px;
    padding:14px 18px;margin-bottom:20px;font-size:13.5px;line-height:1.6;color:#cdd6e4}
  .thesis .lbl{color:#5fd0d0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;display:block;margin-bottom:5px}
  .status{background:#101a13;border:1px solid #1f3a28;border-left:3px solid #5fd07e;border-radius:10px;
    padding:13px 18px;margin-bottom:20px;font-size:13.5px;line-height:1.55;color:#d8ecdc}
  .status .lbl{color:#5fd07e;font-size:11px;text-transform:uppercase;letter-spacing:.6px;display:block;margin-bottom:5px}
  .legend{display:flex;gap:16px;flex-wrap:wrap;color:#8a8f98;font-size:11.5px;margin:0 0 18px}
  .legend span{display:flex;gap:6px;align-items:center} .ldot{width:11px;height:11px;border-radius:50%}
  .epic{background:#171a22;border:1px solid #262b36;border-radius:12px;padding:15px 18px;margin-bottom:15px}
  .ehead{display:flex;gap:11px;align-items:center}
  .eid{flex-shrink:0;font-family:ui-monospace,Menlo,monospace;font-size:12px;font-weight:700;color:#9db4d6;
    background:#1c2331;border:1px solid #2f3645;border-radius:7px;padding:3px 9px}
  .etitle{font-size:15px;font-weight:700;margin-right:auto}
  .esum{color:#9aa1ad;font-size:12.5px;margin:4px 0 11px 0}
  .badge{padding:2px 9px;border-radius:6px;font-size:11px;font-weight:600;white-space:nowrap}
  .badge.ok{background:#163a22;color:#5fd07e} .badge.bad{background:#3a1616;color:#ef7a7a}
  .badge.mid{background:#3a2f16;color:#e6c98a} .badge.muted{background:#222734;color:#9aa1ad}
  .badge.dep{background:#241820;color:#a87a93;border:1px solid #4a2a3d}
  .row{display:flex;gap:11px;align-items:baseline;padding:7px 0;border-top:1px solid #20242e;cursor:pointer}
  .row:first-of-type{border-top:none} .row:hover .rlabel{color:#fff}
  .dot{flex-shrink:0;width:12px;height:12px;border-radius:50%;align-self:flex-start;margin-top:5px}
  .dot.ok{background:#5fd07e} .dot.bad{background:#ef7a7a} .dot.mid{background:#e6c98a} .dot.muted{background:#3a4150}
  .dot.dep{background:#6e4257}
  .caret{display:inline-block;width:11px;color:#717a88;transition:transform .12s;font-size:10px}
  .row.exp .caret{transform:rotate(90deg)}
  .row.depr .rlabel{color:#9a8290;text-decoration:line-through;text-decoration-color:#5a3a48}
  .rlabel{font-size:13px;color:#e6e6e6;margin-right:auto}
  .rref{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:#717a88;flex-shrink:0;
    max-width:42%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .detail{display:none;margin:0 0 6px 23px;padding:10px 13px;background:#10131a;border:1px solid #222734;
    border-left:2px solid #2f3645;border-radius:7px}
  .detail.open{display:block}
  .dtext{font-size:12.5px;line-height:1.6;color:#c4ccd8;margin-bottom:9px}
  .specbtn{font:600 11.5px ui-monospace,Menlo,monospace;color:#9fe0a5;background:#16261b;
    border:1px solid #2f5238;border-radius:6px;padding:4px 11px;cursor:pointer}
  .specbtn:hover{background:#1d3325} .specbtn:disabled{color:#5a6270;background:#191b22;border-color:#262b36;cursor:default}
  .sec{font-size:13px;font-weight:700;color:#cdd6e4;margin:26px 0 10px;border-bottom:1px solid #262b36;padding-bottom:6px}
  /* modal */
  #ov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.62);z-index:50}
  #mo{display:none;position:fixed;top:4%;left:50%;transform:translateX(-50%);width:min(920px,93vw);max-height:90vh;
      background:#10131a;border:1px solid #2f3645;border-radius:10px;flex-direction:column;z-index:51}
  #mo header{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid #262b36}
  #mo h3{margin:0;font:12.5px ui-monospace,Menlo,monospace;color:#9fe0a5;word-break:break-all}
  #mo .x{cursor:pointer;color:#8a8f98;font-size:22px;line-height:1}
  #mo pre{margin:0;padding:16px;overflow:auto;white-space:pre-wrap;word-break:break-word;
    font:12.5px/1.58 ui-monospace,Menlo,monospace;color:#cdd6e4}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def resolve(ref: str):
    """Return the on-disk Path for a spec ref, or None (incl. the '—' sentinel)."""
    if ref == "—":
        return None
    for cand in (REPO / ref, REPO / "backlog" / ref):
        if cand.is_file():
            return cand
    return None


def current_status() -> str:
    """The high-level, one-sentence project status block for the top of the page.

    Edit the STATUS constant to update. Strictly user-facing: keep eval-internal
    mechanics and agent-facing constraints OUT of this — they don't belong on the
    public roadmap.
    """
    return f'<div class="status"><span class="lbl">Current status</span>{STATUS}</div>'


def render() -> str:
    cards, sources = [], []
    for e in EPICS:
        rows = []
        specs = sorted(e["specs"], key=lambda s: SORT_RANK.get(s[0], 1))
        for i, (st, label, ref, detail) in enumerate(specs):
            sid = f'{e["id"]}-{i}'
            path = resolve(ref)
            if path is not None:
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except Exception as ex:  # noqa: BLE001
                    content = f"(could not read {ref}: {ex})"
                sources.append(f'<div id="src-{sid}">{esc(content)}</div>')
                btn = (f'<button class="specbtn" onclick="openSpec(\'{sid}\',\'{esc(ref)}\')">'
                       f'open full spec ↗</button>')
            else:
                btn = '<button class="specbtn" disabled>tracked by task #</button>'
            ref_html = "" if ref == "—" else f'<span class="rref">{esc(ref)}</span>'
            rowcls = "row depr" if st in ("deprecated", "rejected") else "row"
            rows.append(
                f'<div class="{rowcls}" onclick="tog(this)"><div class="dot {STATUS_CLASS[st]}"></div>'
                f'<div class="rlabel"><span class="caret">▶</span> {esc(label)}</div>{ref_html}</div>'
                f'<div class="detail"><div class="dtext">{esc(detail)}</div>{btn}</div>'
            )
        b = STATUS_CLASS[e["status"]]
        cards.append(
            f'<div class="epic"><div class="ehead">'
            f'<span class="eid">{e["id"]}</span>'
            f'<span class="etitle">{esc(e["title"])}</span>'
            f'<span class="badge {b}">{STATUS_LABEL[e["status"]]}</span></div>'
            f'<div class="esum">{esc(e["summary"])}</div>'
            f'{"".join(rows)}</div>'
        )

    legend = (
        '<div class="legend">'
        '<span><i class="ldot" style="background:#5fd07e"></i> done</span>'
        '<span><i class="ldot" style="background:#e6c98a"></i> in progress</span>'
        '<span><i class="ldot" style="background:#ef7a7a"></i> blocked</span>'
        '<span><i class="ldot" style="background:#3a4150"></i> to do</span>'
        '<span><i class="ldot" style="background:#6e4257"></i> deprecated</span>'
        '<span style="margin-left:auto">click a row for detail · “open full spec” shows the backlog file</span>'
        '</div>'
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Roadmap</title>
<style>{CSS}</style></head><body>
<div class="nav">
  <a href="index.html">Home</a>
  <a href="roadmap.html" class="active">Roadmap</a>
  <a href="task-catalog.html">Task Suite</a>
  <a href="results.html">Results</a>
</div>
<div class="wrap">
<h1>Roadmap — harness-vs-model eval, by epic</h1>
<div class="ts">generated {date.today().isoformat()} · hand-curated from backlog/ · edit tools/roadmap.py to update</div>
<div class="thesis"><span class="lbl">Goal</span>{THESIS}</div>
{current_status()}
<div class="sec" style="margin-top:6px">Epics</div>
{legend}
{''.join(cards)}
</div>
<div id="srcs" style="display:none">{''.join(sources)}</div>
<div id="ov" onclick="closeSpec()"></div>
<div id="mo"><header><h3 id="mo-title"></h3><span class="x" onclick="closeSpec()">×</span></header><pre id="mo-pre"></pre></div>
<script>
function tog(r){{var d=r.nextElementSibling;if(d&&d.classList.contains('detail')){{d.classList.toggle('open');r.classList.toggle('exp');}}}}
function openSpec(sid,title){{var el=document.getElementById('src-'+sid);if(!el)return;
  document.getElementById('mo-title').textContent=title;
  document.getElementById('mo-pre').textContent=el.textContent;
  document.getElementById('ov').style.display='block';document.getElementById('mo').style.display='flex';}}
function closeSpec(){{document.getElementById('ov').style.display='none';document.getElementById('mo').style.display='none';}}
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeSpec();}});
</script>
</body></html>"""


def main():
    OUT.write_text(render(), encoding="utf-8")
    n_specs = sum(len(e["specs"]) for e in EPICS)
    n_embedded = sum(1 for e in EPICS for s in e["specs"] if resolve(s[2]) is not None)
    print(f"wrote {OUT} ({n_specs} specs / {len(EPICS)} epics; {n_embedded} full specs embedded)")


if __name__ == "__main__":
    main()
