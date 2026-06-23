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
Each spec row: (status, label, ref, detail).
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
    "Prove the suite can detect a <b>HARNESS</b> difference (openclaw vs hermes) "
    "independent of the <b>MODEL</b>. Both harnesses run the same model "
    "(<span class='mono'>deepseek-v4-pro</span>), so any score gap is the harness. "
    "Until the suite demonstrably <i>can</i> discriminate, no “the harnesses are "
    "equivalent” conclusion is valid."
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
            ("deprecated", "Install-during-trial adapter — DEPRECATED 2026-06-02 (was task #84)", "2026-05-28-tau3-bench-integration.md",
             "Deprecated. The thin adapter runs the BAKED harness and doesn't forward Harbor's injected mcp_servers, so the tau3-runtime MCP never reaches the agent; closing that needs an install-during-trial / MCP-forwarding adapter. Decided not worth building for a single benchmark — tau3 is retained as oracle-only pipeline validation, the live agent-run is out of scope. This was the last open E1 item, so the epic's runtime/adapter foundation is complete."),
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
             "Both harnesses wired to a shared headless Chromium on the memory host (CDP :9222). 2026-06-03 REAL ROOT CAUSE (supersedes BOTH the CDP-reachability guess AND the embedded-vs-gateway theory): the rich image shipped a STALE persisted plugin registry (/root/.openclaw/plugins) indexed before the `browser` plugin's deps were present, so browser (+ canvas/file-transfer/phone-control/talk-voice) were never indexed and their tools never surfaced — embedded OR gateway-backed. Fix is one line baked into the image: `openclaw plugins registry --refresh` (46 → 64 enabled). Proven in-container: after refresh, plain embedded `openclaw agent --local` exposes the identical 59-tool catalog as gateway-backed (browser + full hindsight memory + sessions_spawn/subagents + 14 skills). Embedded is NOT a reduced runtime for anything the core-11 exercises — so the prior 'must go gateway-backed' conclusion was wrong (see the row below)."),
            ("done", "Self-contained in-container browser (no cross-machine CDP)", "2026-06-03-self-contained-browser.md",
             "The browser tool drove a shared Chromium on <MEMORY-HOST> (CDP :9222) over the LAN — a cross-machine dependency that violated the self-contained requirement (and accidentally disabled each harness's own local browser). Fixed: bake a real `/usr/bin/chromium` (148) into the rich image + `/etc/chromium.d` no-sandbox flags (run-as-root) + an idempotent `start-cdp.sh` that launches a headless Chromium INSIDE each trial container; both harnesses' browser tools attach to `127.0.0.1:9222`. One controlled browser backend per container keeps the comparison fair (only the harness's tool differs). Verified e2e: openclaw 1.0 / 13 calls, hermes 1.0 / 60 calls, trajectory shows `127.0.0.1` and ZERO <memory-host> refs (prior run had 18). Memory (hindsight :8888) is still the shared <memory-host> substrate by design — separate decision."),
            ("rejected", "Gateway-backed full-harness execution — NOT NEEDED (was the #90 theory)", "2026-06-03-gateway-backed-full-harness.md",
             "Spec written on a premise that the experiments disproved. The theory: thin `--local` runs EMBEDDED, dropping the gateway's browser control server → no browser tool. Reality: the blocker was the stale plugin registry (row above); once refreshed, embedded `--local` exposes browser + memory + the full 59-tool catalog identically to gateway-backed. The gateway adds only channels/cron/device-pairing/multi-session-routing/sidecars — none of which the core-11 tasks touch. Operator decision (2026-06-03): ship the registry-refresh fix, KEEP the embedded `--local` invocation (simpler, no gateway lifecycle / port-collision / teardown risk, and proven fair). Gateway-backed left as rejected, not deferred — there is no capability gap to close."),
        ],
    },
    {
        "id": "E4", "status": "partial",
        "title": "Task Suite",
        "summary": "Build the tests AND prove they measure the harness, not the model — authoring and validity are one feedback loop, so they're one epic. Author a task, review it, and if it's blunt it routes straight back to re-authoring; the goal is a suite that genuinely separates the harnesses, ending in the verdict grid.",
        "specs": [
            # ── authoring: the categories, shapes, and task instances ──
            ("partial", "Task suite design — categories, shapes, first-sweep selection", "2026-05-27-task-suite-design.md",
             "The taxonomy: ~10 categories × shapes and which subset runs in the first sweep. A living document as shapes are added, sharpened, or retired."),
            ("done", "Context-management category — long-session behaviour", "2026-05-27-context-management-category.md",
             "How the agent behaves as its context window fills — eviction, update-churn, cross-talk — sized to overflow the operative window so the harness has to compact/externalise. Promoted out of DEFERRED 2026-05-30."),
            ("partial", "Multi-step task suite — design + specs", "2026-05-28-multi-step-tasks.md",
             "Harbor multi-step tasks whose per-step setup.sh can wipe scratch state between steps, forcing state to survive via the harness memory rather than the filesystem."),
            ("done", "Sub-agent spawning + research tasks", "2026-05-29-new-eval-tasks-subagent-research.md",
             "Two shapes shipped 2026-05-30: a sub-agent fan-out task (N non-batchable prose problems so parallel delegation beats serial, reward = fraction solved) and a research task."),
            ("partial", "Goal-oriented real-world workflows", "2026-05-30-goal-oriented-real-world-tasks.md",
             "Workflows modelled on how users actually drive agents (3 shapes + a simulator). The category was built (task #83) but the spec is still PROPOSED — design is settling."),
            ("done", "tau3-bench integration — oracle shipped; agent-run deprecated", "2026-05-28-tau3-bench-integration.md",
             "Integrate the tau3 benchmark. The oracle ships and validates the eval pipeline. The live agent-run was DEPRECATED 2026-06-02 — the thin adapter doesn't forward Harbor's injected tau3-runtime MCP, and an install-during-trial adapter isn't worth building for one benchmark (see the E1 adapter row). tau3 is retained as oracle-only; closed as scoped."),
            # ── discrimination & validity: do the authored tasks actually measure the harness? ──
            ("partial", "Harness-vs-model discriminating suite — instrument proven (interim)", "2026-05-30-harness-vs-model-discriminating-suite.md",
             "The core spec: evaluate the SCAFFOLDING, not the LLM. Proven interim — a precision-memory task split openclaw 12/12 vs hermes 8/12 (Δ=0.33) with a visible memory failure in hermes's trajectory. The n=5 pass^k verdict is pending the E2 fixes."),
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
            ("todo", "Rework the ~22 salvageable deprecated tasks (task #89)", "—",
             "The deprecated-but-salvageable tasks still need the difficulty + de-telegraph treatment before they re-enter the discriminating grid. Tracked as task #89."),
            ("done", "Context-rot scoring integrity — false-zero audit + metric normalization", "2026-06-02-context-rot-scoring-integrity.md",
             "A hermes context-rot-02 trial scored 0 after recalling all 8 chains correctly — its staged write never landed in /app, so the verifier read an empty file (a false zero that faked a 0.875-vs-0 gap; hermes actually beat openclaw 8/8 vs 7/8). SHIPPED: recall graders now archive answer.md + emit numeric answer_present (0 = VOID, not wrong); reward.json kept dict[str,float|int] (a string field silently drops the trial from the viewer). Recorded result hand-corrected (stopgap; real fix = re-run via task #92). SHIPPED (task #93): reward.json now carries ONLY normalized [0,1] keys with identical names on both tasks — reward, correctness, and early/middle/late as per-depth fractions (so the rot curve compares across rot-01's 4/bucket and rot-02's 2-3/bucket). Raw counts (facts/chains) + the answer audit (answer_present/answer_chars) moved to a sibling reward-details.json that Harbor never aggregates — killing the cross-task blend (chains=(0+8)/2=4.0, answer_chars 85→42.5 masquerading as a score). All three scoring-integrity deliverables shipped; the lone residual — re-running existing trials under the new keys — is owned by #92 (write-persistence) + the #81 verdict grid, not this work."),
            ("done", "Core suite — the 11 load-bearing harness-measuring tests", "2026-06-03-core-suite-selection.md",
             "Designated the CORE comparison set: 11 tasks, one per harness-distinct capability, anchored on the three PROVEN discriminators (memory-conversational-01 Δ0.50, failure-recovery-loop-01 1.0-vs-0.0, tool-sprawl-precision-01 efficiency 3-vs-7 calls). Same model both harnesses ⇒ any gap is the harness. Coverage: memory ×3 (recall-under-load / proactive-write+correction / stale-vs-live-file), long-context ×2 (compaction-on-overflow / in-window rot), control-loop ×2 (recovery+retry / mid-task replan), tool-precision ×1 (selection among 57 decoys, F1), delegation+skill ×2 (sub-agent fan-out / skill discovery), stateful workflow ×1 (ledger edit w/ preservation traps). Excludes prompt-injection (model-level safety, not harness) + the wt-0.5 model-dominated families; top alternates (find-contradictions, factual-lookup-cited) named for swap-in if a task fails to separate. Wired as configs/core-suite.yaml + structurally validated (all 11 paths/graders resolve; runner honors CONFIG/N_ATTEMPTS/JOB_NAME). n=1 separation run pending the image rebuild."),
            ("done", "Recall MCP dropped from both eval harnesses — memory substrate change", "2026-06-03-core-suite-selection.md",
             "recall (Graphiti temporal-KG memory, <memory-host>:8408) was erroring on every hermes invocation, so it was removed from BOTH harness configs (openclaw.json mcp.servers + hermes config.yaml mcp_servers) to keep the comparison fair and unblocked — hindsight kept in both, hermes honcho untouched, and the memory host recall server itself left intact (the harnesses just no longer mount it). New substrate: openclaw=hindsight vs hermes=honcho+hindsight. Consequence: the old Δ0.50 memory-conversational-01 baseline is VOID (measured on the recall-bearing substrate) — RESULTS.md 'Known asymmetries' + the proven-discriminator note both corrected. Takes effect after a harbor-agents-rich rebuild. Commits 597070b + 8f812e1."),
            ("done", "Hermes write-persistence (#92) — false-zero root cause fixed", "2026-06-02-context-rot-scoring-integrity.md",
             "The context-rot-02 false-zero: hermes's write_file reported 85 bytes but /app/answer.md was empty at verify. Root cause = hermes's file tools are workspace-rooted at the terminal backend's cwd (`terminal.cwd: \".\"`); the adapter never cd'd to the task workdir, so writes landed in a cwd-shadow the verifier (reading /app) never saw — while openclaw's direct write landed. Fix (lib/hermes_thin.py, commit e1c4541): `cd /app && hermes …`. Verified via the file-persistence-01 probe (tasks/_verify): hermes answer_present 0→1, reward 1.0, alongside openclaw 1.0 + oracle 1.0. The probe is a reusable write-persistence regression."),
            ("done", "Verifier-integrity audit — all 54 tasks; 2 proven discriminators GAMEABLE", "2026-06-09-verifier-integrity-audit.md",
             "7-agent audit of every task's grader for forge surface. HEADLINE: two of the three proven discriminators can be FAKED — failure-recovery-loop-01 (success string baked in an agent-readable script + plantable payload.txt → full reward without the recovery path) and tool-sprawl-precision-01 (tool_f1 read from a chmod-666 log the agent can append to). 11 live gameable tasks (Wave 1), ~21 rewardkit-only modernization, ~21 leave-as-is (code-editing already /opt/canonical tamper-guarded). A gameable discriminator silently invalidates the thesis — validity-critical."),
            ("done", "rewardkit grading rollout — all 23 active graded tasks converted + validated", "2026-06-09-verifier-sandbox-rollout.md",
             "Operator directive: rewardkit is the grading framework — RE-IMPLEMENT bespoke bash/python graders cleanly in it (most of FOOTGUNS is bespoke-grader bugs), keep bespoke only for pytest tasks. rewardkit BAKED into harbor-agents-rich:latest (+ canonical Dockerfile) so shared-mode conversion = just reward.py + test.sh + oracle --force-build. ALL 23 active graded tasks DONE + oracle-validated (verified criterion counts, $0 OpenRouter) across patterns: additive, penalty max(0,found-fp)/N (weight-1 score + weight-0 detail), F1-blend, binary, blend, net-penalty UPDATE-trap, line-anchored cross-talk, and positional lost-in-the-middle recall. 12 single-step + 11 multistep (the recall-step reward.py grades; multi_step_reward_strategy=final). #93 context-rot rot-curve fractions + answer_present preserved as weight-0 criteria. Footguns found: zero-arg criteria double-register (#45); vestigial verifier.env breaks grading. Only the 4 pytest tasks stay bespoke (by design). Separate-verifier sandbox (environment_mode=separate, FOOTGUNS #42) used where isolation is needed; isolation alone doesn't fix a forged artifact (#44). 5 commits local on the run host main pending operator push."),
            ("todo", "Run n≥3 pass^k grid → verdict (task #81)", "—",
             "The verdict run: pass^k (all-of-k) across the core suite, because n=1 is a coin-toss and the harness signal is reliability variance + efficiency. Numbers are auto-computed by metrics/track_a_weighted.py → track_a_report.json (split + pass^k + per-category + efficiency); the verdict layer on top is the thin RESULTS.md (see E5). Gated on the E2 fixes + the image rebuild + the Wave-1 verifier-integrity fixes (a gameable discriminator must be closed before its numbers are trusted). Tracked as task #81."),
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
            ("todo", "RESULTS.md — thin verdict over the auto-computed report (task #81)", "2026-06-03-results-verdict-thin-over-report.md",
             "Retargeted 2026-06-03 (option a): the numbers are owned by Harbor reporting + metrics/track_a_weighted.py → track_a_report.json (split, pass^k, per-category, efficiency — auto-computed, never hand-typed, no drift/false-zero risk). RESULTS.md is demoted to the THIN layer no automated report can produce: the plain-English verdict + construct-validity caveats (honcho asymmetry, recall-removed, BLUNT controls, false-zero/VOID traps) + reproduction command, embedding the auto-computed split block and linking to the viewer. Written once the first core-suite grid runs."),
            ("todo", "FE exportable verdict report (follow-up)", "2026-06-03-results-verdict-thin-over-report.md",
             "Extend the front-end (viewer / dashboards) to EMIT an exportable verdict file — a 'Download report' that bundles the split + pass^k + caveats into a standalone artifact, so the verdict isn't a manual paste. When it ships, RESULTS.md becomes the export target (or is generated by it). Deferred until after the first verdict run."),
        ],
    },
]

# ── The 11 core tests — how each one actually works ───────────────────────────
# Sequential, one per harness-distinct capability (configs/core-suite.yaml). Each
# entry: number, task slug, capability axis, a short scoring tag (right-rail), and
# the expandable trap / scoring / harness-isolation detail. `ev` = discrimination
# evidence status: "ok" = mechanics built + oracle-clean; "mid" = built but the Δ
# must be RE-EARNED on the hindsight-only substrate (the three 2026-06-10 reworks).
CORE_TESTS_INTRO = (
    "Every core test is built from the same four parts, so once you see the pattern you can read all 11. "
    "<b>(1) A surface goal stated like a real user</b> — no hint of the trap, the hidden check, or the "
    "required strategy (“no telegraphing”). <b>(2) A hidden mechanism that makes the answer "
    "uncomputable without the harness</b>, enforced <i>mechanically</i> by a step's "
    "<span class='mono'>setup.sh</span> — it wipes all scratch before grading, silently rewrites a file, "
    "strips a value that was only ever spoken, or gates on latency. <b>(3) A graded scorer</b> "
    "(<span class='mono'>tests/test.sh</span>) — partial credit across weighted dimensions, never pass/fail "
    "(binary tasks saturate to 1.0 for two competent harnesses). <b>(4) The kill test</b> — if "
    "<span class='mono'>python3 -c</span> or one file-read could solve it, it measures the <i>model</i>; "
    "every core task defeats this. A <span class='mono'>0</span> on a <i>completed</i> run is VOID, not a "
    "loss — weight-0 <span class='mono'>diagnostics</span> tell the two apart."
)

CORE_TESTS = [
    {"group": "Memory ×3 — state must survive a filesystem wipe, through the harness", "tests": [
        {"n": 1, "ev": "mid", "name": "multistep-memory-conversational-01", "axis": "recall precision under distraction",
         "score": "correct / 12",
         "trap": "Learns 12 of Dana's facts, then 4 distractor turns inject confusable siblings (Sam's allergy, Jess's red Honda…); step 07's setup.sh wipes all scratch + deletes /app before the recall, so answers must come from harness memory alone.",
         "scoring": "reward = correct / 12. A precise fact = 1.0; stating the distractor value or hedging both ≈ 0.33. Flat 0.0 if the wipe assertion fails (VOID).",
         "why": "No scratch survives between steps — only the harness's session memory does."},
        {"n": 2, "ev": "ok", "name": "true-multi-turn-memory-write-01", "axis": "proactive memory update on correction",
         "score": "(correct/8) × (0.85+0.15·dinner)",
         "trap": "Mid-conversation the user CORRECTS two facts (timezone Pacific→Mountain, climbing nights Tue/Thu/Sat→Mon/Wed/Fri); the next step wipes scratch. Passive listening keeps the stale values.",
         "scoring": "reward = (correct_fields / 8) × (0.85 + 0.15·dinner_ok); the dinner plan must respect the CORRECTED constraints. Stale values score 0.",
         "why": "A model can't force the harness to write/update memory — without an UPDATE the old values survive the wipe."},
        {"n": 3, "ev": "ok", "name": "multistep-stale-memory-vs-file-01", "axis": "trust the live file over stale memory",
         "score": "1.0 iff 275 (not 45)",
         "trap": "Agent reads & repeatedly computes with cache_ttl_seconds: 45 (cementing it in memory); step 04's setup.sh SILENTLY rewrites the file to 275 (then deletes itself) and asks for the current value.",
         "scoring": "reward = 1.0 iff the answer is 275 AND not also 45 — dumping both forfeits it (an honest “275 (was 45)” is carved out).",
         "why": "The silent rewrite forces a choice between repeatedly-used memory (45) and a re-fetch (275); bare code never sees the change."},
    ]},
    {"group": "Long-context ×2 — retention as the window fills", "tests": [
        {"n": 4, "ev": "ok", "name": "multistep-context-fill-02", "axis": "final-vs-stale value under window overflow",
         "score": "max(0, current−stale) / 12",
         "trap": "18 weekly reports (~1.3M tokens, >1× the 1M window); nearly every fact is corrected 2–3× over the quarter (lead Reyes→Tanaka→Okafor…). Reports deleted before recall.",
         "scoring": "reward = max(0, current_hits − stale_hits) / 12. Each fact: +1 for the FINAL value with ≤1 prior value present; −1 for adopting the GCP decoy. Dumping churned values = 0.",
         "why": "A script can't tell the final value from a stale one buried mid-context under saturation — it needs the harness to manage retention across 18 steps."},
        {"n": 5, "ev": "ok", "name": "context-rot-02", "axis": "multi-hop lost-in-the-middle recall",
         "score": "matched / 8",
         "trap": "18 inspection records (~345K — FITS the window, so this tests retention not overflow) threaded into one growing conversation; 8 questions each chain two facts buried at different depths via a bridge entity.",
         "scoring": "reward = matched / 8; each needle must be positional + exclusive. Weight-0 early/middle/late fractions trace the rot curve.",
         "why": "Resolving a two-hop chain across facts at different conversational depths needs the harness's threaded context, not offline lookup."},
    ]},
    {"group": "Control loop ×2 + Tool precision ×1 — recovery, replanning, selection", "tests": [
        {"n": 6, "ev": "mid", "name": "failure-recovery-loop-01", "axis": "adaptive error-recovery ladder",
         "score": "0.6·correct + 0.4·efficiency",
         "trap": "dfetch fails with 4 DIFFERENT actionable errors in sequence (bad-region→401→stale-lock→success); correct values are found only by exploring /app/dfetch.conf. Success emits an HMAC nonce whose secret lives in the stripped binary — forged answers fail --verify; the binary sha256 is pinned against swaps.",
         "scoring": "reward = 0.6·correctness + 0.4·efficiency, where efficiency = clamp((18−calls)/(18−3)). 1.0 = HMAC-verified files + an ordered progression log ending in “release”, ≤18 calls.",
         "why": "Each error demands interaction with live system state; there's no static answer, and only correct sequential calls unlock the secret."},
        {"n": 7, "ev": "ok", "name": "plan-then-revise-01", "axis": "retain a bound across a mid-task context wipe",
         "score": "clamp 0.40 + fn 0.40 + cleanup 0.12 + replan 0.08",
         "trap": "A numeric clamp bound [−1000, 1000] is stated ONLY in conversation in steps 1–2; step 3's setup.sh strips the helper and the bound from disk + instructions, then asks for a refactor that must re-apply it. Leaked scratch notes → reward 0.0.",
         "scoring": "reward = clamp_memory 0.40 + functional 0.40 + cleanup 0.12 + replan 0.08. Without recalling the bound, the score caps ≈ 0.60.",
         "why": "The bound is unrecoverable from step 3's files/instructions — only harness-threaded conversation state unlocks the full score."},
        {"n": 8, "ev": "mid", "name": "tool-sprawl-precision-01", "axis": "tool selection among decoys",
         "score": "0.5·F1 + 0.5·efficiency",
         "trap": "60 tools, exactly 3 correct (opaque names — function only in --help); 9 name-collision decoys (count, analyze, rank) match the verbs but do the wrong thing. The answer VALUE is deliberately not scored (a script could compute it) — only logged tool invocations are.",
         "scoring": "reward = 0.5·selection_F1 + 0.5·call_efficiency. Computing offline without invoking tools = 0.0 (VOID).",
         "why": "Grading is purely on invocation discipline; a pure python3 solver scores 0."},
    ]},
    {"group": "Delegation + skill acquisition ×2", "tests": [
        {"n": 9, "ev": "ok", "name": "sub-agent-parallel-decompose-01", "axis": "parallel sub-agent fan-out",
         "score": "correct / 60",
         "trap": "60 independent problems, each needing a value from a latency-gated binary (8s/call). Serial = 60×8s = 480s, blowing the 600s timeout even with instant math; only parallel sub-agent sessions clear enough in time.",
         "scoring": "reward = correct / 60. No concurrency bonus — a serial harness simply finishes fewer (mtime logs are advisory only).",
         "why": "A single synchronous token-stream hits a hard 480s floor; only independent parallel sessions beat the clock."},
        {"n": 10, "ev": "ok", "name": "skill-discovery-and-use-01", "axis": "find the right skill by reading metadata",
         "score": "passed / 16",
         "trap": "13 skills; only tabular-shape-report is correct — and its name does NOT echo “shape”, while 3 better-named decoys emit near-miss output. The required --null=empty flag is documented only in the right SKILL.md. A SHA256 breadcrumb proves real discovery; running all 13 (brute sweep) trips a gate and denies credit.",
         "scoring": "reward = passed / 16 (8 files × {correct, discovered}). Near-miss = 1/2; swept = 0/2.",
         "why": "Discovery needs parsing structured tool metadata, not reasoning; the sweep gate + hash breadcrumb block reimplementation cheats."},
    ]},
    {"group": "Stateful workflow ×1", "tests": [
        {"n": 11, "ev": "ok", "name": "update-record-with-cleanup-01", "axis": "precise multi-axis ledger edit",
         "score": "per-decision / N",
         "trap": "A 340-row budget CSV; the agent must DISCOVER the dedup rule (identical date+vendor+amount+category) by inspection — never told. 6 May grocery dup-groups to remove, 7 lookalike groups (near-amounts 55.00/55.10, same-date-different-category…) to PRESERVE, plus a rent row to split 50/50. No answer key ever exists in the container.",
         "scoring": "reward = (dedup + preserve + rent_split + rent_orig_gone + collateral) / total, per decision — with a dedup gate that floors preserve/collateral at 0 if nothing was actually deduped (so “do nothing” can't score ≈0.5).",
         "why": "Requires empirically inferring the rule from the data, then a precise stateful transform — there's no key to learn from."},
    ]},
]

STATUS_LABEL = {"done": "done", "partial": "in progress", "blocked": "blocked",
                "todo": "to do", "deprecated": "deprecated", "rejected": "rejected"}
STATUS_CLASS = {"done": "ok", "partial": "mid", "blocked": "bad",
                "todo": "muted", "deprecated": "dep", "rejected": "dep"}

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
  .now{background:#1a1712;border:1px solid #3a2f16;border-left:3px solid #e6c98a;border-radius:10px;
    padding:13px 18px;font-size:12.8px;line-height:1.6;color:#e8dcc2}
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


def render_core_tests() -> str:
    """The 11 core tests as a sequential accordion (reuses .row/.detail + tog())."""
    blocks = []
    for grp in CORE_TESTS:
        rows = []
        for t in grp["tests"]:
            rows.append(
                f'<div class="row" onclick="tog(this)">'
                f'<div class="dot {t["ev"]}" title="{"built + oracle-clean" if t["ev"]=="ok" else "built; Δ to re-earn"}"></div>'
                f'<div class="rlabel"><span class="caret">▶</span> '
                f'<b>{t["n"]}.</b> <span class="mono">{esc(t["name"])}</span> — {esc(t["axis"])}</div>'
                f'<span class="rref">{esc(t["score"])}</span></div>'
                f'<div class="detail"><div class="dtext">'
                f'<b>Trap:</b> {esc(t["trap"])}<br>'
                f'<b>Scoring:</b> {esc(t["scoring"])}<br>'
                f'<b>Harness-only:</b> {esc(t["why"])}'
                f'</div></div>'
            )
        blocks.append(
            f'<div class="epic"><div class="ehead">'
            f'<span class="etitle" style="font-size:13.5px">{esc(grp["group"])}</span></div>'
            f'{"".join(rows)}</div>'
        )
    return "".join(blocks)


def render() -> str:
    cards, sources = [], []
    for e in EPICS:
        rows = []
        for i, (st, label, ref, detail) in enumerate(e["specs"]):
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
  <a href="agent-status.html">Agent status</a>
  <a href="task-catalog.html">Task Suite</a>
  <a href="roadmap.html" class="active">Roadmap</a>
</div>
<div class="wrap">
<h1>Roadmap — harness-vs-model eval, by epic</h1>
<div class="ts">generated {date.today().isoformat()} · hand-curated from backlog/ · edit tools/roadmap.py to update</div>
<div class="thesis"><span class="lbl">The thesis</span>{THESIS}</div>
<div class="sec" style="margin-top:6px">Where we stand right now</div>
<div class="now"><b>rewardkit grading rollout (2026-06-10) — COMPLETE: all 23 active graded tasks converted + oracle-validated.</b>
Per operator directive, rewardkit is now the grading framework: bespoke bash/python graders are
RE-IMPLEMENTED cleanly as rewardkit criteria (most of FOOTGUNS is bespoke-grader bugs). rewardkit is
<i>baked</i> into <span class="mono">harbor-agents-rich:latest</span>, so a conversion is just
<span class="mono">reward.py</span> + <span class="mono">test.sh</span> + an oracle
<span class="mono">--force-build</span>. <b>All 23 active graded tasks done</b> — 12 single-step +
11 multistep recall (the recall-step <span class="mono">reward.py</span> grades) — spanning
additive, penalty <span class="mono">max(0,found-fp)/N</span> (weight-1 score + weight-0 detail),
F1-blend, binary, blend, net-penalty UPDATE-trap, line-anchored cross-talk, and positional
lost-in-the-middle recall (the #93 rot-curve fractions + <span class="mono">answer_present</span>
preserved as weight-0 criteria). Each oracle-validated with a verified criterion count, <b>$0
OpenRouter</b>. Footguns found + documented: zero-arg criteria double-register (#45); a vestigial
<span class="mono">verifier.env</span> LLM key breaks grading. <b>Keep bespoke:</b> the 4 pytest
tasks (rewardkit would just wrap pytest). 5 commits sit on the run host <span class="mono">main</span>
pending the operator's push (no GitHub auth in the non-interactive session).<br><br>
<b>Verifier-integrity (2026-06-09) — TWO of three proven discriminators were
GAMEABLE</b> (now fixed). Adopting Harbor's native <span class="mono">environment_mode="separate"</span> verifier
sandbox (prototyped on skill-discovery; the broken prototype is now fixed + oracle-validated, with
rewardkit <i>baked</i> into the verifier image — no per-trial PyPI fetch). A 7-agent audit of all 54
tasks found the headline risk: <span class="mono">failure-recovery-loop-01</span> (success string
baked in an agent-readable script + plantable <span class="mono">payload.txt</span>) and
<span class="mono">tool-sprawl-precision-01</span> (<span class="mono">tool_f1</span> read from a
<span class="mono">chmod-666</span> log) can be FAKED without exercising the measured capability — a
gameable discriminator silently invalidates the thesis. <b>Key caveat:</b> isolation alone does NOT
fix a forged artifact (FOOTGUNS #44); each gameable task also needs its grader re-sourced from the
un-forgeable trajectory or a recomputed read-only input. <b>Threat-model refinement (2026-06-10):</b>
this eval measures HONEST harnesses, so the real priority is <i>honest shortcut</i> (a capable agent
reads a baked answer — a KILL-test fail) over <i>adversarial forge</i> (fabricating a log honest
harnesses never touch). DONE + oracle-validated tonight: <span class="mono">unit-tests-01</span>
(mutant answer-key relocated env→tests/) and <span class="mono">failure-recovery-loop-01</span>
(plaintext payload → token-derived; the proven discriminator now passes the KILL test, honest
behavior unchanged). Adversarial-forge tasks deprioritized (low value for an honest-harness verdict);
<span class="mono">schedule-meeting</span> deferred (needs a sidecar redesign — see
backlog/2026-06-10-overnight…). New: <span class="mono">NORTH_STAR.md</span> (canonical value
hierarchy). <b>Gates the n≥3 verdict (#81)</b> — failure-recovery needs a supervised re-baseline.<br><br>
<b>#90 (browser) is fixed — and the fix overturned its own spec.</b> Chasing the
missing <span class="mono">browser</span> tool, the embedded-vs-gateway theory was <i>disproven</i>
in-container: the real blocker was a <b>stale persisted plugin registry</b> baked into the rich
image (indexed before the browser plugin's deps existed → browser + canvas/file-transfer/etc.
never indexed). One line baked into the image — <span class="mono">openclaw plugins registry
--refresh</span> (46 → 64 enabled) — and the <span class="mono">browser</span> tool surfaces.
Proven: plain embedded <span class="mono">openclaw agent --local</span> then exposes the
<i>identical</i> 59-tool catalog as gateway-backed (browser + full hindsight memory + sub-agent
tools + skills). Embedded is NOT a reduced runtime for anything the core-11 exercises, so the
gateway-backed work is <b>rejected, not deferred</b> — there's no capability gap to close.
<b>Operator decision (2026-06-03):</b> registry-refresh + keep embedded. <b>Validity caveat:</b>
prior runs lacked the browser tool, so only <i>browser-dependent</i> tasks need re-baselining —
the rest of the catalog was always present.<br><br>
<b>Already done</b> (E2 cleared + scoring solid): both harnesses pinned to <b>novita</b>
(privacy-intact, deny+tool-use+reasoning); hermes write-persistence (<b>#92</b>) fixed +
verified; <b>core-11</b> defined; context-rot scoring (<b>#93</b>) fixed; recall removed
(substrate openclaw=hindsight vs hermes=honcho+hindsight); browser tool (<b>#90</b>) fixed via
registry refresh. <b>Sequence:</b> confirm hermes browser parity → run core-11 n=1 separation
→ n≥3 pass^k → thin verdict (E5).</div>
<div class="sec">Epics</div>
{legend}
{''.join(cards)}
<div class="sec" style="margin-top:30px">The 11 core tests — how each one measures the harness</div>
<div class="thesis"><span class="lbl">How every test works</span>{CORE_TESTS_INTRO}</div>
<div class="legend">
  <span><i class="ldot" style="background:#5fd07e"></i> mechanics built + oracle-clean</span>
  <span><i class="ldot" style="background:#e6c98a"></i> built; Δ to re-earn (2026-06-10 rework)</span>
  <span style="margin-left:auto">click a test for its trap · scoring · why it's the harness, not the model</span>
</div>
{render_core_tests()}
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
