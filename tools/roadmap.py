#!/usr/bin/env python3
"""Generate roadmap.html — the plan + progress for the harbor-tasks harness-vs-model
eval, broken out by EPIC.

Sibling of tools/task_catalog.py (the TASKS) and tools/agent_status.py (the
HARNESSES). This page is the PLAN: the thesis, the epics, every backlog spec that
rolls up under each epic, and its status. Content is hand-curated — edit the EPICS
table below (each spec row points at its backlog/ file) and re-run:

    python3 tools/roadmap.py     # writes roadmap.html

Keep it clear and concise. Spec statuses mirror the backlog frontmatter badges.
"""
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "roadmap.html"

THESIS = (
    "Prove the suite can detect a <b>HARNESS</b> difference (openclaw vs hermes) "
    "independent of the <b>MODEL</b>. Both harnesses run the same model "
    "(<span class='mono'>deepseek-v4-pro</span>), so any score gap is the harness. "
    "Until the suite demonstrably <i>can</i> discriminate, no “the harnesses are "
    "equivalent” conclusion is valid."
)

# status: done | partial | blocked | todo
# Each spec row: (status, label, backlog-file-or-note)
EPICS = [
    {
        "id": "E1", "status": "done",
        "title": "Harness runtime & adapters",
        "summary": "Run both harnesses identically on Harbor — the foundation everything else sits on.",
        "specs": [
            ("done", "Harbor adoption — retire rube, build on Harbor", "done/2026-05-27-harbor-adoption.md"),
            ("done", "Agent adapters — pre-baked image + NoInstall + OpenRouter", "done/2026-05-27-agent-adapters.md"),
            ("done", "Thin adapters — invoke the BAKED harness, no config rewrite", "done/2026-05-29-thin-adapters.md"),
            ("done", "Pre-built rich harness images (configs + skills + tools)", "done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md"),
            ("done", "openclaw reasoning on OpenRouter — resolved", "done/2026-05-28-openclaw-reasoning-RESOLVED.md"),
        ],
    },
    {
        "id": "E2", "status": "blocked",
        "title": "Fair-comparison controls",
        "summary": "Same model, same provider, isolated state — so a score gap is the harness, not luck.",
        "specs": [
            ("blocked", "Deterministic provider pin — one shared OpenRouter host",
             "BROKEN: only:[deepseek] is invalid → 404; fix = fireworks/novita (operator picks)"),
            ("done", "Cost + token tracking — per-trial usage at live pricing", "done/2026-05-27-cost-and-token-tracking.md"),
            ("done", "Memory-state wipe hook — reset harness memory at trial start", "hooks/wipe_memory_state.py"),
        ],
    },
    {
        "id": "E3", "status": "partial",
        "title": "Capability infrastructure (memory + browser)",
        "summary": "The subsystems the harnesses actually use — recall memory and a shared browser.",
        "specs": [
            ("done", "Eval memory stack — <memory-host> deployment, LAN-reachable", "done/2026-05-29-memory-stack-deployment.md"),
            ("done", "Recall — bge-m3 embedder + extractor + community-build", "done/2026-05-29-recall-bge-m3-and-eval-ontology.md"),
            ("done", "Recall — hindsight-style tool surface (P1–P4)", "done/2026-05-29-recall-hindsight-style-plugin.md"),
            ("done", "Hermes dual-plugin activation", "done/2026-05-29-hermes-dual-plugin-system.md"),
            ("partial", "Eval infra stack — memory shipped, browser portion", "2026-05-29-eval-infra-stack.md"),
            ("blocked", "Browser tool enablement — openclaw tool not surfacing (task #90)", "2026-06-02-browser-and-pin-findings.md"),
        ],
    },
    {
        "id": "E4", "status": "partial",
        "title": "Task suite authoring",
        "summary": "Build the tests — the categories and shapes that exercise harness behaviour.",
        "specs": [
            ("partial", "Task suite design — categories, shapes, first-sweep selection", "2026-05-27-task-suite-design.md"),
            ("done", "Context-management category — long-session behaviour", "2026-05-27-context-management-category.md"),
            ("partial", "Multi-step task suite — design + specs", "2026-05-28-multi-step-tasks.md"),
            ("done", "Sub-agent spawning + research tasks", "2026-05-29-new-eval-tasks-subagent-research.md"),
            ("partial", "Goal-oriented real-world workflows", "2026-05-30-goal-oriented-real-world-tasks.md"),
            ("partial", "tau3-bench integration — oracle passes; agent-run deferred (#84)", "2026-05-28-tau3-bench-integration.md"),
        ],
    },
    {
        "id": "E5", "status": "partial",
        "title": "Discrimination & validity",
        "summary": "The frontier: make the suite actually MEASURE the harness, then run the verdict grid.",
        "specs": [
            ("partial", "Harness-vs-model discriminating suite — instrument proven (interim)", "2026-05-30-harness-vs-model-discriminating-suite.md"),
            ("done", "Methodology evidence base — approach grounded in published work", "2026-06-01-methodology-evidence-base.md"),
            ("done", "Discrimination-hardening sweep — difficulty is the lever", "2026-05-31-discrimination-hardening-session.md"),
            ("done", "Adversarial review — only ~4 genuine discriminators found", "2026-06-01-adversarial-review.md"),
            ("done", "Telegraphing audit — 37/50 leaked the trap; all fixed", "2026-06-01-telegraphing-audit.md"),
            ("done", "Retired-task coverage matrix — no capability left untested", "2026-06-01-retired-task-coverage-matrix.md"),
            ("todo", "Rework the ~22 salvageable deprecated tasks (task #89)", "—"),
            ("todo", "Run n≥3 pass^k grid → RESULTS.md verdict (task #81)", "—"),
        ],
    },
    {
        "id": "E6", "status": "partial",
        "title": "Observability & reporting",
        "summary": "See the state at a glance, and publish the verdict.",
        "specs": [
            ("done", "Agent-status dashboard — the two harnesses", "done/2026-05-29-agent-status-dashboard.md"),
            ("done", "Task-catalog page — visual index of every task", "2026-05-31-task-catalog-page.md"),
            ("done", "Roadmap page — this page", "tools/roadmap.py"),
            ("todo", "RESULTS.md — the discrimination verdict (task #81)", "—"),
        ],
    },
]

STATUS_LABEL = {"done": "done", "partial": "in progress", "blocked": "blocked", "todo": "to do"}
STATUS_CLASS = {"done": "ok", "partial": "mid", "blocked": "bad", "todo": "muted"}

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
  .legend span{display:flex;gap:6px;align-items:center}
  .ldot{width:11px;height:11px;border-radius:50%}
  .epic{background:#171a22;border:1px solid #262b36;border-radius:12px;padding:15px 18px;margin-bottom:15px}
  .ehead{display:flex;gap:11px;align-items:center}
  .eid{flex-shrink:0;font-family:ui-monospace,Menlo,monospace;font-size:12px;font-weight:700;color:#9db4d6;
    background:#1c2331;border:1px solid #2f3645;border-radius:7px;padding:3px 9px}
  .etitle{font-size:15px;font-weight:700;margin-right:auto}
  .esum{color:#9aa1ad;font-size:12.5px;margin:4px 0 11px 0}
  .badge{padding:2px 9px;border-radius:6px;font-size:11px;font-weight:600;white-space:nowrap}
  .badge.ok{background:#163a22;color:#5fd07e} .badge.bad{background:#3a1616;color:#ef7a7a}
  .badge.mid{background:#3a2f16;color:#e6c98a} .badge.muted{background:#222734;color:#9aa1ad}
  .row{display:flex;gap:11px;align-items:baseline;padding:6px 0;border-top:1px solid #20242e}
  .row:first-of-type{border-top:none}
  .dot{flex-shrink:0;width:12px;height:12px;border-radius:50%;align-self:flex-start;margin-top:5px}
  .dot.ok{background:#5fd07e} .dot.bad{background:#ef7a7a} .dot.mid{background:#e6c98a} .dot.muted{background:#3a4150}
  .rlabel{font-size:13px;color:#e6e6e6;margin-right:auto}
  .rref{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:#717a88;flex-shrink:0;
    max-width:46%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .sec{font-size:13px;font-weight:700;color:#cdd6e4;margin:26px 0 10px;border-bottom:1px solid #262b36;padding-bottom:6px}
  .now{background:#1a1712;border:1px solid #3a2f16;border-left:3px solid #e6c98a;border-radius:10px;
    padding:13px 18px;font-size:12.8px;line-height:1.6;color:#e8dcc2}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render() -> str:
    cards = []
    for e in EPICS:
        rows = []
        for st, label, ref in e["specs"]:
            ref_html = "" if ref == "—" else f'<span class="rref">{esc(ref)}</span>'
            rows.append(
                f'<div class="row"><div class="dot {STATUS_CLASS[st]}"></div>'
                f'<div class="rlabel">{esc(label)}</div>{ref_html}</div>'
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
        '<span style="margin-left:auto" class="mono">refs → backlog/&lt;file&gt;</span>'
        '</div>'
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Roadmap</title>
<style>{CSS}</style></head><body>
<div class="nav">
  <a href="agent-status.html">Agent status</a>
  <a href="task-catalog.html">Task catalog</a>
  <a href="roadmap.html" class="active">Roadmap</a>
</div>
<div class="wrap">
<h1>Roadmap — harness-vs-model eval, by epic</h1>
<div class="ts">generated {date.today().isoformat()} · hand-curated from backlog/ · edit tools/roadmap.py to update</div>
<div class="thesis"><span class="lbl">The thesis</span>{THESIS}</div>
{legend}
{''.join(cards)}
<div class="sec">Where we stand right now</div>
<div class="now">Epics 1–6 are largely built, but we're stuck at the <b>E2 fairness gate</b>: we
can't run a trustworthy comparison until the <b>provider pin</b> (E2) and <b>openclaw browser</b>
(E3) are fixed. Next two actions — (1) operator picks the pin host (fireworks / novita);
(2) diagnose openclaw browser surfacing (task #90). One image rebuild then unblocks the
E5 verdict grid (n≥3 pass^k → RESULTS.md). Detail:
<span class="mono">backlog/2026-06-02-browser-and-pin-findings.md</span>.</div>
</div>
</body></html>"""


def main():
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT} ({sum(len(e['specs']) for e in EPICS)} specs across {len(EPICS)} epics)")


if __name__ == "__main__":
    main()
