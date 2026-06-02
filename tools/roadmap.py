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
        "id": "E2", "status": "blocked",
        "title": "Fair-comparison controls",
        "summary": "Same model, same provider, isolated state — so a score gap is the harness, not luck.",
        "specs": [
            ("blocked", "Deterministic provider pin — one shared OpenRouter host",
             "done/2026-05-27-deterministic-provider-routing.md",
             "Both harnesses must hit ONE OpenRouter upstream or cost/cache differ run-to-run. The pin regressed to an invalid slug `only:[deepseek]` → 404: hermes can't call at all, openclaw silently routes free — so NEITHER is actually pinned. Fix: a valid non-training host (fireworks or novita, both 200 / 1M ctx); operator picks, then rebuild the image."),
            ("done", "Cost + token tracking — per-trial usage at live pricing", "done/2026-05-27-cost-and-token-tracking.md",
             "Per-trial token + dollar cost from live OpenRouter pricing, including cache-write tokens. This is what surfaces the efficiency signal — openclaw spends ~0.35–0.62× hermes's cost for equal results on the same model."),
            ("done", "Memory-state wipe hook — reset harness memory at trial start", "hooks/wipe_memory_state.py",
             "Wipes the harness memory backend at TrialEvent.START so a memory task must re-derive state THROUGH the harness, not inherit it from a prior trial. Scoped to eval groups only."),
        ],
    },
    {
        "id": "E3", "status": "partial",
        "title": "Capability infrastructure (memory + browser)",
        "summary": "The subsystems the harnesses actually use — recall memory and a shared browser.",
        "specs": [
            ("done", "Eval memory stack — wiley deployment, LAN-reachable", "done/2026-05-29-memory-stack-deployment.md",
             "Recall / Graphiti memory services deployed on wiley and reachable from the eval network (8408/8888) so trials can exercise the harnesses' long-term memory."),
            ("done", "Recall — bge-m3 embedder + extractor + community-build", "done/2026-05-29-recall-bge-m3-and-eval-ontology.md",
             "Re-embedded prod groups with bge-m3 + a deepseek-v4-flash extractor and scheduled community detection — the memory substrate both harnesses read and write against."),
            ("done", "Recall — hindsight-style tool surface (P1–P4)", "done/2026-05-29-recall-hindsight-style-plugin.md",
             "Four phases: coaching tool descriptions, a reflect tool, bank config + directives, and mental-models + a refresher cron with row-locking — the surface the agent uses to store and recall facts."),
            ("done", "Hermes dual-plugin activation", "done/2026-05-29-hermes-dual-plugin-system.md",
             "Investigated and activated hermes's two independent plugin systems so it exposes the same capability classes openclaw does."),
            ("partial", "Eval infra stack — memory shipped, browser portion", "2026-05-29-eval-infra-stack.md",
             "The combined memory + browser infra spec. The memory half shipped; the browser half is the open item below."),
            ("blocked", "Browser tool enablement — openclaw tool not surfacing (task #90)", "2026-06-02-browser-and-pin-findings.md",
             "Both harnesses are wired to a shared headless Chromium on wiley (CDP :9222). hermes exposes browser_navigate; openclaw's `browser` tool does NOT surface despite browser.enabled:true — prime suspect is CDP reachability from inside the trial container. browser-find-fact-01 is the gated task that proves the path once it works."),
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
            ("todo", "Run n≥3 pass^k grid → RESULTS.md verdict (task #81)", "—",
             "The verdict run: pass^k (all-of-k) across the discriminating set, because n=1 is a coin-toss and the harness signal is reliability variance + efficiency. Gated on the E2 fixes. Tracked as task #81."),
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
            ("todo", "RESULTS.md — the discrimination verdict (task #81)", "—",
             "The published verdict: does the instrument detect a harness difference, and how big? Written once the E4 grid runs. Tracked as task #81."),
        ],
    },
]

STATUS_LABEL = {"done": "done", "partial": "in progress", "blocked": "blocked",
                "todo": "to do", "deprecated": "deprecated"}
STATUS_CLASS = {"done": "ok", "partial": "mid", "blocked": "bad",
                "todo": "muted", "deprecated": "dep"}

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
            rowcls = "row depr" if st == "deprecated" else "row"
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
<div class="now">Epics 1–6 are largely built, but we're stuck at the <b>E2 fairness gate</b>: we
can't run a trustworthy comparison until the <b>provider pin</b> (E2) and <b>openclaw browser</b>
(E3) are fixed. Next two actions — (1) operator picks the pin host (fireworks / novita);
(2) diagnose openclaw browser surfacing (task #90). One image rebuild then unblocks the
E4 verdict grid (n≥3 pass^k → RESULTS.md). Detail:
<span class="mono">backlog/2026-06-02-browser-and-pin-findings.md</span>.</div>
<div class="sec">Epics</div>
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
