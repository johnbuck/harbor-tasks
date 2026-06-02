#!/usr/bin/env python3
"""Generate roadmap.html — the plain-language plan + progress for the harbor-tasks
harness-vs-model eval.

Sibling of tools/task_catalog.py (the TASKS) and tools/agent_status.py (the
HARNESSES). This page is the PLAN: the thesis, the four phases, what's done, and
what's blocking the next trustworthy run. Content is hand-curated (a narrative, not
drift-derived) — edit the PHASES / MILESTONES tables below and re-run:

    python3 tools/roadmap.py     # writes roadmap.html

Keep it clear and simple. One screen of "where we stand."
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
PHASES = [
    {
        "n": "1",
        "title": "Make the tasks genuinely discriminating",
        "status": "partial",
        "summary": "The tasks now measure the harness, not instruction-following or memorized answers.",
        "items": [
            ("done", "Methodology grounded in published evidence",
             "Harness-vs-model separation supported (Terminal-Bench, Aider, METR); pass^k is the right reliability metric (τ-bench); “telegraphing” = a construct-validity threat."),
            ("done", "Adversarial review of all 50 tasks",
             "Found only ~4 genuine harness discriminators; ~23 model-dominated one-shots deprecated (pending operator review); a few outright broken."),
            ("done", "Fixed telegraphing — the #1 validity bug",
             "37 of 50 tasks leaked the trap they secretly measured. All fixed across 7 waves; load-bearing constraints now enforced mechanically, not by instruction."),
            ("done", "Built / hardened real discriminators",
             "context-rot family, sub-agent fan-out redesign (reward = fraction solved), cover-task hardenings (tool-selection, tool-sprawl, plan-then-revise), and browser-find-fact-01 (the only task routing through the harness browser-tool layer)."),
            ("done", "Drift-proof catalog + deprecation handling",
             "task-catalog.html regenerates from the on-disk tree; runner auto-excludes status=deprecated tasks."),
            ("todo", "Rework the ~22 salvageable deprecated tasks (task #89)",
             "The KILL set was deprecated non-destructively; the salvageable ones still need the hardening treatment before they re-enter the grid."),
        ],
    },
    {
        "n": "2",
        "title": "Make the comparison FAIR (infra correctness)",
        "status": "blocked",
        "summary": "Two infra facts must be true before ANY run is trustworthy. Both are currently broken — this is the live blocker.",
        "items": [
            ("blocked", "Fix the provider pin",
             "only:[“deepseek”] is an invalid OpenRouter slug → 404. hermes can't make a single call; openclaw silently routes free → neither harness is actually pinned, so cost/cache comparisons are void. Fix identified (fireworks or novita — both 200, non-training, 1M ctx); operator picks the host."),
            ("blocked", "Make openclaw actually USE the browser (task #90)",
             "browser.enabled:true is baked but the tool doesn't surface at runtime. Prime suspect: CDP <memory-host>:9222 unreachable from inside the trial container."),
            ("done", "Both harnesses wired to a shared headless Chromium",
             "openclaw browser.cdpUrl + hermes browser.cdp_url → <memory-host>:9222 (live Chrome 148). Capabilities baked into the image (thin adapters ignore Harbor-injected mcp_servers)."),
        ],
    },
    {
        "n": "3",
        "title": "Run the real grid",
        "status": "todo",
        "summary": "Gated on Phase 2.",
        "items": [
            ("todo", "n≥3 pass^k across the discriminating set",
             "n=1 is a coin-toss — the harness signal is reliability variance + efficiency (cost at equal quality), not single-run reward. Run browser-e2e first as the smoke test."),
        ],
    },
    {
        "n": "4",
        "title": "Publish the verdict + Track B",
        "status": "todo",
        "summary": "Not started.",
        "items": [
            ("todo", "RESULTS.md — the discrimination verdict",
             "Synthesize the grid: does the instrument detect a harness difference, and how big?"),
            ("todo", "Stand up Track B (general capability)",
             "The second comparison track, separate from the harness-discrimination track."),
        ],
    },
]

# A short, honest timeline of what's been built (most recent first).
MILESTONES = [
    ("2026-06-02", "browser-find-fact-01 + browser enablement; broken-pin diagnosis documented"),
    ("2026-06-01", "Adversarial review, telegraphing audit (37 fixed), evidence base, context-rot family"),
    ("2026-05-31", "Discrimination-hardening sweep: difficulty is the lever; graded scoring + crash penalty + catalog"),
    ("earlier", "Suite defined (~10 categories), thin adapters, rich image, recall + browser infra, provider-pin work, 5 established benchmarks integrated"),
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
  .wrap{max-width:980px}
  .mono{font-family:ui-monospace,Menlo,monospace}
  .thesis{background:#13182098;border:1px solid #2a3550;border-left:3px solid #5fd0d0;border-radius:10px;
    padding:14px 18px;margin-bottom:22px;font-size:13.5px;line-height:1.6;color:#cdd6e4}
  .thesis .lbl{color:#5fd0d0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;display:block;margin-bottom:5px}
  .phase{background:#171a22;border:1px solid #262b36;border-radius:12px;padding:16px 18px;margin-bottom:16px}
  .phead{display:flex;gap:12px;align-items:center;margin-bottom:4px}
  .pnum{flex-shrink:0;width:30px;height:30px;border-radius:8px;background:#1c2331;border:1px solid #2f3645;
    display:flex;align-items:center;justify-content:center;font-weight:700;color:#9db4d6}
  .ptitle{font-size:15px;font-weight:700;margin-right:auto}
  .psum{color:#9aa1ad;font-size:12.5px;margin:2px 0 12px 42px}
  .badge{padding:2px 9px;border-radius:6px;font-size:11px;font-weight:600;white-space:nowrap}
  .badge.ok{background:#163a22;color:#5fd07e} .badge.bad{background:#3a1616;color:#ef7a7a}
  .badge.mid{background:#3a2f16;color:#e6c98a} .badge.muted{background:#222734;color:#9aa1ad}
  .item{display:flex;gap:11px;padding:8px 0 8px 42px;border-top:1px solid #20242e}
  .item:first-of-type{border-top:none}
  .dot{flex-shrink:0;width:14px;height:14px;border-radius:50%;margin-top:3px}
  .dot.ok{background:#5fd07e} .dot.bad{background:#ef7a7a} .dot.mid{background:#e6c98a} .dot.muted{background:#3a4150}
  .itxt b{font-size:13px;color:#e6e6e6;font-weight:600}
  .itxt .d{display:block;color:#9aa1ad;font-size:12px;margin-top:2px}
  .sec{font-size:13px;font-weight:700;color:#cdd6e4;margin:26px 0 10px;border-bottom:1px solid #262b36;padding-bottom:6px}
  .ms{display:flex;gap:14px;padding:7px 0;border-top:1px solid #20242e}
  .ms:first-of-type{border-top:none}
  .ms .when{flex-shrink:0;width:96px;color:#8a8f98;font-size:12px;font-family:ui-monospace,Menlo,monospace}
  .ms .what{font-size:12.5px;color:#cdd6e4}
  .legend{display:flex;gap:16px;flex-wrap:wrap;color:#8a8f98;font-size:11.5px;margin:18px 0 4px}
  .legend span{display:flex;gap:6px;align-items:center}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render() -> str:
    phases = []
    for p in PHASES:
        items = []
        for st, title, desc in p["items"]:
            items.append(
                f'<div class="item"><div class="dot {STATUS_CLASS[st]}"></div>'
                f'<div class="itxt"><b>{esc(title)}</b><span class="d">{esc(desc)}</span></div></div>'
            )
        b = STATUS_CLASS[p["status"]]
        phases.append(
            f'<div class="phase"><div class="phead">'
            f'<div class="pnum">{p["n"]}</div>'
            f'<div class="ptitle">{esc(p["title"])}</div>'
            f'<span class="badge {b}">{STATUS_LABEL[p["status"]]}</span></div>'
            f'<div class="psum">{esc(p["summary"])}</div>'
            f'{"".join(items)}</div>'
        )

    milestones = "".join(
        f'<div class="ms"><div class="when">{esc(w)}</div><div class="what">{esc(t)}</div></div>'
        for w, t in MILESTONES
    )

    legend = (
        '<div class="legend">'
        '<span><i class="dot ok" style="width:12px;height:12px;border-radius:50%"></i> done</span>'
        '<span><i class="dot mid" style="width:12px;height:12px;border-radius:50%"></i> in progress</span>'
        '<span><i class="dot bad" style="width:12px;height:12px;border-radius:50%"></i> blocked</span>'
        '<span><i class="dot muted" style="width:12px;height:12px;border-radius:50%"></i> to do</span>'
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
<h1>Roadmap — harness-vs-model eval</h1>
<div class="ts">generated {date.today().isoformat()} · hand-curated · edit tools/roadmap.py to update</div>
<div class="thesis"><span class="lbl">The thesis</span>{THESIS}</div>
{legend}
{''.join(phases)}
<div class="sec">Where we stand right now</div>
<div class="phase" style="border-color:#3a2f16">
  <div class="psum" style="margin-left:0">Phases 1's tasks are sharp, but we're stuck at the <b>Phase 2 gate</b>:
  we can't run a trustworthy comparison until the <b>provider pin</b> and <b>openclaw browser</b> are fixed.
  Next two actions — (1) operator picks the pin host (fireworks / novita); (2) diagnose openclaw browser
  surfacing (task #90). One image rebuild then fixes both → first trustworthy both-harness result.
  Detail: <span class="mono">backlog/2026-06-02-browser-and-pin-findings.md</span>.</div>
</div>
<div class="sec">Milestones so far</div>
{milestones}
</div>
</body></html>"""


def main():
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
