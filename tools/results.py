#!/usr/bin/env python3
"""Generate results.html — the public head-to-head harness results browser.

Reads the Track-A analyzer reports (``track_a_report.json``) for a curated set
of paired sweeps and bakes a self-contained, dark-theme page (matching
roadmap.html / task-catalog.html) with a RUN SWITCHER: pick any run, old or
new, and see that run's head-to-head.

Each run is shown with its TRUE validation status (Latest / Superseded / …) so
nothing masquerades as a finalized verdict — an umbrella note states plainly
that no validated n>=3 verdict exists for the current tasks yet. This mirrors
RESULTS.md, the project's validation-state source of truth.

Public + outcome-focused by design:
  * harnesses are named (openclaw vs hermes);
  * efficiency is shown as RELATIVE ratios (e.g. 6.8x cost) — never absolute $;
  * the model is kept generic ("the same frontier model");
  * deep eval mechanics stay light.

To refresh / add a run: edit the RUNS list below + re-run this script. The
analyzer writes its report into the ``<job>__openclaw`` dir, comparing the
paired ``__hermes`` / ``__openclaw`` runs.

Nothing host-identifying is read or emitted — only aggregate numbers and
harness / category names. Run tools/check_topology.sh on the output before
publishing, same as the other dashboards.
"""

import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOBS = REPO / "jobs"
OUT = REPO / "results.html"

HE = "hermes"
OC = "openclaw"

# ---- curated runs, newest first (edit + re-run to refresh) ------------------
# status: "latest" | "superseded" | "historical"
RUNS = [
    {"job": "suite-n1", "label": "Unified suite smoke", "date": "2026-06-25", "status": "latest"},
    {"job": "smoke-n1", "label": "Full-suite smoke", "date": "2026-06-22", "status": "superseded"},
    {"job": "core-suite-n5", "label": "Core verdict", "date": "2026-06-10", "status": "superseded"},
    {"job": "core-suite-n1", "label": "Core smoke", "date": "2026-06-10", "status": "superseded"},
]

STATUS_META = {  # label, chip-class, dot-color
    "latest": ("Latest", "ok", "#5fd07e"),
    "superseded": ("Superseded", "dep", "#c98a5f"),
    "historical": ("Historical", "muted", "#8a8f98"),
}

REL_ORDER = [
    ("clean", "clean", "#5fd07e"),
    ("partial", "partial", "#e6c98a"),
    ("timeout", "timeout", "#7f9fc8"),
    ("fail", "fail", "#ef7a7a"),
    ("crash", "crash", "#b5403f"),
]

CSS = """
*{box-sizing:border-box}
body{font:14px/1.6 system-ui,sans-serif;margin:0;background:#0f1117;color:#e6e6e6;padding:24px}
.wrap{max-width:1000px;margin:0 auto}
a{color:#9db4d6}
h1{font-size:18px;margin:0 0 2px}
.ts{color:#8a8f98;font-size:12px;margin-bottom:18px}
.muted{color:#8a8f98}

.nav{display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
.nav a{font-size:13px;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:4px 12px;color:#9db4d6}
.nav a:hover{background:#1c2331}
.nav a.active{background:#1b2a1f;border-color:#3a5a44;color:#9fe0a5;font-weight:600}

/* run switcher */
.swlbl{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#8a8f98;margin-bottom:8px}
.runsel{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.runtab{cursor:pointer;background:#10131a;border:1px solid #2f3645;border-radius:11px;padding:10px 14px;
  min-width:184px;text-align:left;font:inherit;color:inherit;transition:border-color .12s,background .12s}
.runtab:hover{background:#161b24;border-color:#3a4350}
.runtab.active{background:#15201a;border-color:#3a5a44;box-shadow:inset 0 0 0 1px #21331f}
.runtab .rl{font:700 13px ui-monospace,Menlo,monospace;color:#e6e6e6;display:flex;align-items:center;gap:7px}
.runtab.active .rl{color:#9fe0a5}
.runtab .rdot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.runtab .rm{font-size:11px;color:#8a8f98;margin-top:4px;font-family:ui-monospace,Menlo,monospace}
.runtab .rchip{margin-left:auto;font:700 9.5px system-ui,sans-serif;text-transform:uppercase;letter-spacing:.5px;
  padding:1px 7px;border-radius:20px}
.rchip.ok{background:#163a22;color:#5fd07e}
.rchip.dep{background:#2a1d14;color:#e0a772;border:1px solid #5a3a22}
.rchip.muted{background:#222734;color:#9aa1ad}

/* per-run status banner */
.rbanner{border-radius:9px;padding:11px 15px;margin-bottom:18px;font-size:12.5px;line-height:1.55}
.rbanner.info{background:#10131a;border:1px solid #243043;border-left:3px solid #5fd0d0;color:#c4ccd8}
.rbanner.dep{background:#1a1410;border:1px solid #4a3322;border-left:3px solid #c98a5f;color:#e3d0bd}
.rbanner b{color:#fff}

.ds{margin-top:2px}
.hidden{display:none}

/* hero versus */
.versus{display:grid;grid-template-columns:1fr 132px 1fr;align-items:stretch;
  background:radial-gradient(120% 140% at 50% 0%,#161d26 0%,#13161d 60%);
  border:1px solid #262b36;border-radius:14px;padding:22px 18px;margin-bottom:14px}
.vcol{text-align:center;padding:4px 10px}
.vname{font:700 13px ui-monospace,Menlo,monospace;letter-spacing:.5px;margin-bottom:8px;text-transform:lowercase}
.vcol.he .vname{color:#7fe6a0}
.vcol.oc .vname{color:#9db4d6}
.vscore{font:800 46px/1 system-ui,sans-serif;letter-spacing:-.02em;color:#e6e6e6}
.vcol.lo .vscore{color:#aeb6c2}
.vbar{height:7px;border-radius:4px;background:#222734;margin:12px 8px 0;overflow:hidden}
.vbar i{display:block;height:100%;border-radius:4px}
.vcol.he .vbar i{background:linear-gradient(90deg,#3a8f5a,#5fd07e)}
.vcol.oc .vbar i{background:linear-gradient(90deg,#3f5d86,#9db4d6)}
.vtag{display:inline-block;margin-top:11px;font:700 10px system-ui,sans-serif;text-transform:uppercase;
  letter-spacing:.7px;padding:2px 9px;border-radius:20px}
.vtag.leader.he{background:#13502b;color:#7fe6a0;border:1px solid #2f7a4a}
.vtag.leader.oc{background:#16314f;color:#a8c2e6;border:1px solid #2f4a7a}
.vmid{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;
  border-left:1px solid #232936;border-right:1px solid #232936}
.vvs{font:700 12px ui-monospace,Menlo,monospace;color:#717a88;letter-spacing:1px}
.vgap{font:800 22px system-ui,sans-serif;color:#e6e6e6}
.vgap span{font-size:12px;color:#8a8f98;font-weight:600}
.vmeet{font:700 10.5px system-ui,sans-serif;text-transform:uppercase;letter-spacing:.5px;padding:2px 8px;border-radius:20px}
.vmeet.ok{background:#163a22;color:#5fd07e}
.vmeet.no{background:#222734;color:#9aa1ad}

.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}
@media(max-width:780px){.pillars{grid-template-columns:1fr}.versus{grid-template-columns:1fr 90px 1fr}}
.pill{background:#171a22;border:1px solid #262b36;border-left:3px solid #3a5a44;border-radius:11px;padding:14px 16px}
.pill.oc{border-left-color:#39527a}
.pill .pk{font:700 10.5px system-ui,sans-serif;text-transform:uppercase;letter-spacing:.7px;color:#8a8f98;margin-bottom:9px}
.pill .pv{font:800 27px/1 system-ui,sans-serif;letter-spacing:-.01em;color:#e6e6e6}
.pill .pv .u{font-size:13px;font-weight:700;color:#9aa1ad;margin-left:3px}
.pill .pl{font-size:12px;color:#9fe0a5;font-weight:600;margin-top:4px}
.pill.oc .pl{color:#a8c2e6}
.pill .ps{font-size:12px;line-height:1.5;color:#9aa1ad;margin-top:8px}
.pill .ps b{color:#cdd6e4;font-weight:600}

.sec{font-size:13px;font-weight:700;color:#cdd6e4;margin:24px 0 12px;border-bottom:1px solid #262b36;padding-bottom:6px}
.sec .muted{font-weight:400}

.cats{display:flex;flex-direction:column;gap:8px}
.catrow{background:#171a22;border:1px solid #262b36;border-radius:9px;padding:11px 14px}
.catrow.gap{border-color:#2f4a39}
.cattop{display:flex;align-items:center;gap:9px;margin-bottom:9px}
.catnm{font:700 13px ui-monospace,Menlo,monospace;color:#e6e6e6}
.catw{font-size:11px;color:#717a88}
.gaptag{font:700 10px system-ui,sans-serif;text-transform:uppercase;letter-spacing:.5px;color:#5fd07e;
  background:#143020;border:1px solid #2f5238;border-radius:5px;padding:1px 7px}
.dchip{margin-left:auto;font:700 12px ui-monospace,Menlo,monospace;padding:2px 9px;border-radius:6px}
.dchip.he{background:#13301f;color:#7fe6a0}
.dchip.oc{background:#16263a;color:#9db4d6}
.dchip.tie{background:#222734;color:#9aa1ad}
.hh{display:flex;flex-direction:column;gap:6px}
.hhrow{display:flex;align-items:center;gap:10px}
.hhlbl{width:64px;flex-shrink:0;font:600 11px ui-monospace,Menlo,monospace;color:#8a8f98;text-align:right}
.hbar{flex:1;height:14px;background:#10131a;border-radius:4px;overflow:hidden;border:1px solid #1c2129}
.hbar i{display:block;height:100%;border-radius:3px}
.hbar.he i{background:linear-gradient(90deg,#327a4d,#5fd07e)}
.hbar.oc i{background:linear-gradient(90deg,#39527a,#7f9fc8)}
.hhval{width:38px;flex-shrink:0;font:700 12px ui-monospace,Menlo,monospace;text-align:right}
.hhrow.he .hhval{color:#9fe0a5}
.hhrow.oc .hhval{color:#9db4d6}
.hhrow.lo .hhlbl,.hhrow.lo .hhval{opacity:.72}
.catnote{font-size:12.5px;color:#9aa1ad;margin:12px 2px 0;line-height:1.55}
.catnote b{color:#cdd6e4}

.relgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:680px){.relgrid{grid-template-columns:1fr}}
.relcard{background:#171a22;border:1px solid #262b36;border-radius:10px;padding:13px 15px}
.relhead{display:flex;align-items:baseline;gap:8px;margin-bottom:10px}
.relname{font:700 13px ui-monospace,Menlo,monospace}
.relcard.he .relname{color:#7fe6a0}
.relcard.oc .relname{color:#9db4d6}
.reltri{margin-left:auto;font-size:11.5px;color:#8a8f98}
.reltri b{color:#cdd6e4;font-weight:600}
.relbar{display:flex;height:16px;border-radius:5px;overflow:hidden;background:#10131a;border:1px solid #1c2129}
.relbar i{display:block;height:100%}
.relleg{display:flex;flex-wrap:wrap;gap:10px 14px;margin-top:9px;font-size:11px;color:#9aa1ad}
.relleg span{display:flex;align-items:center;gap:5px}
.rdot{width:9px;height:9px;border-radius:2px;display:inline-block}

.foot{margin-top:30px;border-top:1px solid #262b36;padding-top:14px;font-size:12px;color:#717a88;line-height:1.7}
.foot b{color:#9aa1ad}
.foot a{color:#9db4d6;text-decoration:none}
.foot a:hover{text-decoration:underline}
"""


def load_run(run: dict):
    """Read a run's Track-A report + n_attempts; None if absent."""
    base = JOBS / f"{run['job']}__openclaw"
    rep = base / "suite_report.json"          # post-unify name
    if not rep.exists():
        rep = base / "track_a_report.json"    # pre-unify runs
    if not rep.exists():
        return None
    d = json.loads(rep.read_text())
    cfg = base / "config.json"
    n = 1
    if cfg.exists():
        n = json.loads(cfg.read_text()).get("n_attempts", 1)
    d["_n"] = n
    d["_ntasks"] = d["agents"][HE]["n_tasks"]
    d["_kind"] = "verdict" if n >= 3 else "smoke"
    return d


def relbuckets(counts: dict) -> dict:
    g = {k: 0 for k, _, _ in REL_ORDER}
    for k, v in counts.items():
        if k == "clean":
            g["clean"] += v
        elif k == "partial":
            g["partial"] += v
        elif k.startswith("timeout"):
            g["timeout"] += v
        elif k.startswith("crash"):
            g["crash"] += v
        else:
            g["fail"] += v
    return g


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def hero(d: dict) -> str:
    he = d["agents"][HE]["weighted_aggregate"]
    oc = d["agents"][OC]["weighted_aggregate"]
    sp = d["split"]
    leader = sp["leader"]
    he_cls = "he" + (" win" if he >= oc else " lo")
    oc_cls = "oc" + (" win" if oc > he else " lo")
    he_tag = '<div class="vtag leader he">leads</div>' if leader == HE else ""
    oc_tag = '<div class="vtag leader oc">leads</div>' if leader == OC else ""
    meet = (
        '<div class="vmeet ok">meaningful &#10003;</div>'
        if sp["meets_10pct"]
        else '<div class="vmeet no">within noise</div>'
    )
    return f"""<div class="versus">
  <div class="vcol {he_cls}">
    <div class="vname">{HE}</div><div class="vscore">{he:.2f}</div>
    <div class="vbar"><i style="width:{pct(he)}"></i></div>{he_tag}
  </div>
  <div class="vmid">
    <div class="vvs">vs</div>
    <div class="vgap"><span>&#916;</span> {sp['abs_overall_delta']:.2f}</div>
    {meet}
  </div>
  <div class="vcol {oc_cls}">
    <div class="vname">{OC}</div><div class="vscore">{oc:.2f}</div>
    <div class="vbar"><i style="width:{pct(oc)}"></i></div>{oc_tag}
  </div>
</div>"""


def run_summary(run: dict, d: dict) -> str:
    """Merged status + verdict block, shown directly BELOW the hero result."""
    sp = d["split"]
    he = d["agents"][HE]["weighted_aggregate"]
    oc = d["agents"][OC]["weighted_aggregate"]
    leader = sp["leader"]
    hi, lo = (he, oc) if leader == HE else (oc, he)
    gap = sp["abs_overall_delta"]
    if sp["meets_10pct"]:
        meet = f"a {gap:.2f} gap that clears the 10% bar, separating the two harnesses on the same model"
    else:
        meet = f"a {gap:.2f} gap inside the 10% noise band — no decisive split"

    if run["status"] == "superseded":
        verdict = f"{leader} led the weighted quality score {hi:.2f} to {lo:.2f} — {meet}."
        caveat = (
            "This run predates the task rework (second adversarial pass + rebuild), so it no longer "
            "reflects the current suite — kept for history, not the current state."
        )
        return f'<div class="rbanner dep"><b>Superseded</b> &middot; {run["date"]}. {verdict} {caveat}</div>'

    verdict = f"<b>{leader}</b> leads the weighted quality score {hi:.2f} to {lo:.2f} — {meet}."
    if d["_kind"] == "smoke":
        head = (
            f'<b>Latest run</b> &middot; n=1 smoke, {d["_ntasks"]} tasks ({run["date"]}).'
            if run["status"] == "latest"
            else f'<b>n=1 smoke</b> &middot; {d["_ntasks"]} tasks ({run["date"]}).'
        )
        caveat = (
            "A single attempt per task, though — a preliminary plumbing read, "
            "<b>not a reliability verdict</b>; no task is approved yet, and a few trials hit a "
            "transient outage and are being re-run."
        )
    else:
        head = f'<b>n={d["_n"]} run</b> &middot; {d["_ntasks"]} tasks ({run["date"]}).'
        caveat = (
            f"Passing every attempt on a task: {HE} {pct(d['agents'][HE]['passk_aggregate'])}, "
            f"{OC} {pct(d['agents'][OC]['passk_aggregate'])}."
        )
    return f'<div class="rbanner info">{head} {verdict} {caveat}</div>'


def pillars(d: dict) -> str:
    sp = d["split"]
    he_a, oc_a = d["agents"][HE], d["agents"][OC]

    # quality
    q_leader = sp["leader"]
    q_meet = "meaningful difference &#10003;" if sp["meets_10pct"] else "inside the 10% noise band"
    if d["_kind"] == "verdict":
        q_sub = (
            f"Passing <b>every</b> attempt on a task: {HE} {pct(he_a['passk_aggregate'])}, "
            f"{OC} {pct(oc_a['passk_aggregate'])}. Consistency, not a lucky single run."
        )
    else:
        q_sub = "Single attempt per task — a plumbing read, not a reliability verdict."

    # efficiency (relative only)
    eff = sp.get("efficiency") or {}
    cost_r = eff.get("cost_ratio_oc_over_he")
    tok_r = eff.get("token_ratio_oc_over_he")
    if cost_r:
        eff_costly = OC if cost_r >= 1 else HE
        eff_cheap = HE if cost_r >= 1 else OC
        eff_leader = eff_cheap
        eff_ratio = cost_r if cost_r >= 1 else (1 / cost_r)
        tok_txt = (
            f" It even runs on fewer raw tokens ({pct(tok_r)} of {eff_cheap}'s), so the gap is "
            "how the harness <b>reuses context</b>, not the model."
            if tok_r and tok_r < 1
            else ""
        )
        eff_pv = f'{eff_ratio:.1f}<span class="u">&times; cost/task</span>'
        eff_pl = f"{eff_leader} ahead on cost"
        eff_sub = f"Same model, same work — <b>{eff_costly}</b> spends {eff_ratio:.1f}&times; as much per task.{tok_txt}"
        eff_oc = " oc" if eff_leader == OC else ""
    else:
        eff_pv = '&mdash;<span class="u">cost n/a</span>'
        eff_pl = "not recorded for this run"
        eff_sub = "Per-task cost was not captured in this run's report."
        eff_oc = ""

    # reliability (lower error rate wins)
    he_err = he_a["reliability"].get("error_rate", 0.0)
    oc_err = oc_a["reliability"].get("error_rate", 0.0)
    he_crash = he_a["reliability"].get("crash_rate", 0.0)
    oc_crash = oc_a["reliability"].get("crash_rate", 0.0)
    rel_leader = HE if he_err <= oc_err else OC
    worse = max(he_err, oc_err)
    better = min(he_err, oc_err)
    rel_oc = " oc" if rel_leader == OC else ""

    def cls(leader):
        return " oc" if leader == OC else ""

    return f"""<div class="pillars">
  <div class="pill{cls(q_leader)}">
    <div class="pk">Quality</div>
    <div class="pv">+{sp['abs_overall_delta']:.2f}<span class="u">gap</span></div>
    <div class="pl">{q_leader} ahead &middot; {q_meet}</div>
    <div class="ps">{q_sub}</div>
  </div>
  <div class="pill{eff_oc}">
    <div class="pk">Efficiency</div>
    <div class="pv">{eff_pv}</div>
    <div class="pl">{eff_pl}</div>
    <div class="ps">{eff_sub}</div>
  </div>
  <div class="pill{rel_oc}">
    <div class="pk">Reliability</div>
    <div class="pv">{pct(worse)}<span class="u">vs {pct(better)} errors</span></div>
    <div class="pl">{rel_leader} ahead &middot; fewer failures</div>
    <div class="ps">Crash rate {HE} {pct(he_crash)} vs {OC} {pct(oc_crash)}; overall error rate
      {pct(he_err)} vs {pct(oc_err)}. Lower is more trustworthy unattended.</div>
  </div>
</div>"""


def categories(d: dict) -> str:
    rows = sorted(d["split"]["per_category"], key=lambda c: -c["abs_delta"])
    ncats = len(rows)
    out, ngap = [], 0
    for c in rows:
        he, oc, ad = c[HE], c[OC], c["abs_delta"]
        is_gap = ad >= 0.10
        ngap += is_gap
        leader = HE if he >= oc else OC
        dcls = "he" if he > oc else ("oc" if oc > he else "tie")
        dchip = (
            '<span class="dchip tie">even</span>'
            if he == oc
            else f'<span class="dchip {dcls}">+{ad:.2f} {leader}</span>'
        )
        gaptag = '<span class="gaptag">clear gap</span>' if is_gap else ""
        he_lo = "" if he >= oc else " lo"
        oc_lo = "" if oc > he else " lo"
        out.append(f"""<div class="catrow{' gap' if is_gap else ''}">
  <div class="cattop"><span class="catnm">{c['category']}</span>
    <span class="catw">weight {c['weight']:.1f}</span>{gaptag}{dchip}</div>
  <div class="hh">
    <div class="hhrow he{he_lo}"><span class="hhlbl">{HE}</span>
      <div class="hbar he"><i style="width:{pct(he)}"></i></div><span class="hhval">{he:.2f}</span></div>
    <div class="hhrow oc{oc_lo}"><span class="hhlbl">{OC}</span>
      <div class="hbar oc"><i style="width:{pct(oc)}"></i></div><span class="hhval">{oc:.2f}</span></div>
  </div>
</div>""")
    note = (
        f'<div class="catnote"><b>{ngap} of {ncats} categories</b> show a clear gap (&ge;10%) — '
        "evidence the suite can separate harnesses, the precondition for any &ldquo;they&rsquo;re "
        "equivalent&rdquo; claim. Bars are weighted quality (0&ndash;1) on the same model.</div>"
    )
    return '<div class="cats">' + "\n".join(out) + "</div>" + note


def reliability(d: dict) -> str:
    cards = []
    for ag, cls in ((HE, "he"), (OC, "oc")):
        rel = d["agents"][ag]["reliability"]
        g = relbuckets(rel["counts"])
        total = sum(g.values()) or 1
        segs = "".join(
            f'<i style="width:{g[k] / total * 100:.2f}%;background:{color}" title="{lbl} {g[k]}"></i>'
            for k, lbl, color in REL_ORDER
            if g[k]
        )
        leg = "".join(
            f'<span><i class="rdot" style="background:{color}"></i>{lbl} {g[k]}</span>'
            for k, lbl, color in REL_ORDER
            if g[k]
        )
        cards.append(f"""<div class="relcard {cls}">
  <div class="relhead"><span class="relname">{ag}</span>
    <span class="reltri"><b>{g['clean']}/{total}</b> clean &middot; {pct(rel.get('error_rate', 0.0))} error</span></div>
  <div class="relbar">{segs}</div>
  <div class="relleg">{leg}</div>
</div>""")
    return '<div class="relgrid">' + "\n".join(cards) + "</div>"


def render_dataset(run: dict, d: dict) -> str:
    if d is None:
        return f'<div class="rbanner dep">No report found for <b>{run["label"]}</b> yet.</div>'
    return "\n".join([
        hero(d),
        run_summary(run, d),
        pillars(d),
        '<div class="sec">By category <span class="muted">— weighted quality, sorted by gap</span></div>',
        categories(d),
        '<div class="sec">Reliability <span class="muted">— trial outcomes across all attempts</span></div>',
        reliability(d),
    ])


def runtab(i: int, run: dict, d: dict, active: bool) -> str:
    label_txt, chip_cls, dot = STATUS_META[run["status"]]
    chip = f'<span class="rchip {chip_cls}">{label_txt}</span>'
    if d is None:
        meta = "no report"
    else:
        meta = f"n={d['_n']} &middot; {d['_ntasks']} tasks &middot; {run['date']}"
    return (
        f'<button class="runtab{" active" if active else ""}" data-run="r{i}" onclick="showRun(\'r{i}\')">'
        f'<span class="rl"><i class="rdot" style="background:{dot}"></i>{run["label"]}{chip}</span>'
        f'<span class="rm">{meta}</span></button>'
    )


def aggregate_run(loaded):
    """Synthesize a cross-run aggregate `d` from every run that has a report.

    Reliability = SUMMED raw trial outcomes (legitimately aggregatable).
    Quality / pass^k / efficiency / per-category = MEAN across runs. The shape
    mirrors a real report so hero()/pillars()/categories()/reliability() consume
    it unchanged. Returns (agg_or_None, n_runs_with_reports)."""
    reps = [d for _, d in loaded if d]
    if not reps:
        return None, 0

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else 0.0

    agg = {"agents": {}, "split": {}}
    for ag in (HE, OC):
        counts = {}
        for r in reps:
            for k, v in r["agents"][ag]["reliability"]["counts"].items():
                counts[k] = counts.get(k, 0) + v
        total = sum(counts.values()) or 1
        clean = counts.get("clean", 0)
        crash = sum(v for k, v in counts.items() if k.startswith("crash"))
        agg["agents"][ag] = {
            "weighted_aggregate": mean([r["agents"][ag]["weighted_aggregate"] for r in reps]),
            "passk_aggregate": mean([r["agents"][ag].get("passk_aggregate") for r in reps]),
            "n_tasks": sum(r["agents"][ag]["n_tasks"] for r in reps),
            "reliability": {"counts": counts,
                            "error_rate": (total - clean) / total,
                            "crash_rate": crash / total},
        }

    he_q, oc_q = (agg["agents"][HE]["weighted_aggregate"],
                  agg["agents"][OC]["weighted_aggregate"])
    leader = HE if he_q >= oc_q else OC
    delta = abs(he_q - oc_q)

    cat_acc = {}
    for r in reps:
        for c in r["split"]["per_category"]:
            a = cat_acc.setdefault(c["category"], {HE: [], OC: [], "w": []})
            a[HE].append(c[HE]); a[OC].append(c[OC]); a["w"].append(c.get("weight", 1.0))
    per_cat = [{"category": name, HE: mean(a[HE]), OC: mean(a[OC]),
                "abs_delta": abs(mean(a[HE]) - mean(a[OC])), "weight": mean(a["w"])}
               for name, a in cat_acc.items()]

    def eff_vals(key):
        return [r["split"].get("efficiency", {}).get(key) for r in reps]
    cr, tr = mean(eff_vals("cost_ratio_oc_over_he")), mean(eff_vals("token_ratio_oc_over_he"))
    eff = {"cost_ratio_oc_over_he": cr, "token_ratio_oc_over_he": tr or None} if cr else {}

    agg["split"] = {"leader": leader, "abs_overall_delta": delta,
                    "meets_10pct": delta >= 0.10, "per_category": per_cat, "efficiency": eff}
    agg["_n"] = "agg"
    agg["_ntasks"] = max(r["_ntasks"] for r in reps)
    agg["_kind"] = "verdict" if any(isinstance(r["_n"], int) and r["_n"] >= 3 for r in reps) else "smoke"
    agg["_nruns"] = len(reps)
    agg["_trials"] = sum(sum(agg["agents"][ag]["reliability"]["counts"].values()) for ag in (HE, OC))
    return agg, len(reps)


def aggregate_summary(loaded, agg: dict) -> str:
    """Cross-run banner shown below the aggregate hero — honest about what blends."""
    sp = agg["split"]
    leader = sp["leader"]
    he, oc = agg["agents"][HE]["weighted_aggregate"], agg["agents"][OC]["weighted_aggregate"]
    hi, lo = (he, oc) if leader == HE else (oc, he)
    n_sup = sum(1 for run, d in loaded if d and run["status"] == "superseded")
    sup = f" {n_sup} of them superseded (older task sets)," if n_sup else ""
    return (
        f'<div class="rbanner info"><b>Aggregated across {agg["_nruns"]} runs</b> &middot; '
        f'{agg["_trials"]} total trials. Mean weighted quality <b>{leader}</b> {hi:.2f} vs {lo:.2f}. '
        "Reliability below <b>sums raw trial outcomes</b> across every run (a clean aggregate); "
        f"quality, pass^k and efficiency are per-run <b>means</b> &mdash;{sup} so this is the "
        "cross-run picture, <b>not a finalized verdict</b>. The per-run tabs hold each run&rsquo;s "
        "true status.</div>")


def render_aggregate(loaded, agg: dict) -> str:
    if agg is None:
        return '<div class="rbanner dep">No run reports found to aggregate yet.</div>'
    return "\n".join([
        hero(agg),
        aggregate_summary(loaded, agg),
        pillars(agg),
        '<div class="sec">By category <span class="muted">— mean weighted quality across runs, sorted by gap</span></div>',
        categories(agg),
        '<div class="sec">Reliability <span class="muted">— trial outcomes summed across all runs</span></div>',
        reliability(agg),
    ])


def render() -> str:
    loaded = [(run, load_run(run)) for run in RUNS]
    agg, n_agg = aggregate_run(loaded)
    today = date.today().isoformat()
    agg_active = agg is not None

    agg_tab = (
        '<button class="runtab active" data-run="agg" onclick="showRun(\'agg\')">'
        '<span class="rl"><i class="rdot" style="background:#9b8cff"></i>Aggregated'
        '<span class="rchip muted">all runs</span></span>'
        f'<span class="rm">{n_agg} runs &middot; {agg["_trials"]} trials</span></button>'
    ) if agg_active else ""
    agg_panel = f'<div class="ds" id="agg">{render_aggregate(loaded, agg)}</div>' if agg_active else ""

    tabs = agg_tab + "\n" + "\n".join(
        runtab(i, run, d, (not agg_active) and i == 0) for i, (run, d) in enumerate(loaded))
    panels = agg_panel + "\n" + "\n".join(
        f'<div class="ds{"" if (not agg_active and i == 0) else " hidden"}" id="r{i}">'
        f'{render_dataset(run, d)}</div>'
        for i, (run, d) in enumerate(loaded)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Results</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="nav">
    <a href="index.html">Home</a>
    <a href="roadmap.html">Roadmap</a>
    <a href="task-catalog.html">Task Suite</a>
    <a href="results.html" class="active">Results</a>
  </div>

  <h1>Results — harness head-to-head, same model</h1>
  <div class="ts">generated {today} &middot; <b>openclaw</b> vs <b>hermes</b> on the same frontier model &middot; pick a run to compare &middot; edit tools/results.py to refresh</div>

  <div class="swlbl">View</div>
  <div class="runsel">{tabs}</div>

  {panels}

  <div class="foot">
    <b>How to read this.</b> Both harnesses run the <b>same model</b> under identical conditions, so
    every gap is the harness, not the model. Quality is a weighted 0&ndash;1 score; efficiency is a
    relative ratio; reliability is the spread of trial outcomes. <b>n=1</b> is a single-attempt smoke
    (preliminary); <b>n&ge;3</b> adds pass-every-attempt reliability. A <b>Superseded</b> run predates
    the current task set and is kept only for history.<br>
    Source: <a href="https://github.com/johnbuck/harbor-tasks">github.com/johnbuck/harbor-tasks</a>
    &middot; figures generated from the Track-A analyzer (<code>tools/results.py</code>).
  </div>
</div>
<script>
function showRun(id){{
  document.querySelectorAll('.ds').forEach(function(e){{e.classList.toggle('hidden', e.id!==id);}});
  document.querySelectorAll('.runtab').forEach(function(b){{b.classList.toggle('active', b.dataset.run===id);}});
}}
</script>
</body>
</html>"""


def main():
    OUT.write_text(render(), encoding="utf-8")
    have = [r["job"] for r in RUNS if load_run(r)]
    print(f"wrote {OUT} (runs: {', '.join(have) or 'none found'})")


if __name__ == "__main__":
    main()
