#!/usr/bin/env python3
"""Generate a one-file HTML catalog of every eval task for human review.

Sibling of tools/agent_status.py. Where agent-status.html shows the two HARNESSES,
task-catalog.html shows the TASKS: a visual, drift-proof index of every job/test in
tasks/, with — for each — what is asked (instruction.md), how it's graded (the
verifier + a graded/binary badge), the oracle (solution), and the environment
(Dockerfile), all viewable in-page via the same modal viewer.

Reads ONLY the on-disk repo (task tree + config files) at generate time, so it can't
drift from hand-typed data and needs no docker/network. Self-contained: every
embedded file's contents travel inside the HTML.

Spec: backlog/2026-05-31-task-catalog-page.md

Usage:
    python3 tools/task_catalog.py            # writes task-catalog.html
    python3 tools/task_catalog.py --open     # also opens it in the default browser
"""

import argparse
import json
import re
import tomllib
import webbrowser
from datetime import datetime
from html import escape
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "tasks"
ARCHIVE = REPO / "archive" / "tasks"
OUT = REPO / "task-catalog.html"
WEIGHTS_TOML = REPO / "configs" / "track-a-weights.toml"
FOCUSED_YAML = REPO / "configs" / "track-a-focused.yaml"
MAX = 80000  # per-file embed cap (matches agent_status.py)

# Skip non-task scaffolding directories under tasks/.
SKIP_DIRS = {"_verify"}


def load_weights() -> dict:
    """category -> weight, from configs/track-a-weights.toml (default 1.0)."""
    try:
        data = tomllib.loads(WEIGHTS_TOML.read_text())
        return {k: float(v) for k, v in (data.get("weights") or {}).items()}
    except Exception:
        return {}


def load_focused_names() -> set:
    """Task names listed in configs/track-a-focused.yaml `task_names:` blocks.

    Parsed with a tiny line scanner (no pyyaml dependency) — the file is a flat
    list of `- name` entries under `task_names:` keys.
    """
    names = set()
    try:
        capturing = False
        for line in FOCUSED_YAML.read_text().splitlines():
            s = line.strip()
            if s == "task_names:":
                capturing = True
                continue
            if capturing:
                # A task name is a bare list item with no colon (a mapping like
                # `- path: ...` is NOT a name and ends the block).
                m = re.match(r"-\s+([\w./-]+)\s*$", s)
                if m:
                    names.add(m.group(1))
                else:
                    capturing = False
    except Exception:
        pass
    return names


def read_file(path: Path) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
        if len(txt) > MAX:
            txt = txt[:MAX] + f"\n\n... [truncated at {MAX} chars]"
        return txt
    except Exception as e:
        return f"(could not read {path}: {e})"


# A verifier is "graded" (emits a *fractional* reward) rather than binary. The
# signal is that the reward derives from a fraction — round()/float-division/an
# F1 — NOT from a 0/1 variable like ${correctness} (that's still binary, and
# binary all-or-nothing tasks are the ones that go BLUNT). Heuristic only — the
# embedded verifier source is the ground truth; this just drives the badge.
# Calibrated against every reward-emitting line in tasks/ (2026-05-31).
_GRADED_PATTERNS = [
    re.compile(r"round\s*\("),                  # round(s/6,4), round(net/total)
    re.compile(r"/\s*\$?\{?\w*\s*\d+\.\d"),      # float division: / 8.0, / 2.0
    re.compile(r"\b(f1|fraction|precision|recall)\b", re.I),
]


def is_graded(verifier_texts: list) -> bool:
    blob = "\n".join(verifier_texts)
    return any(p.search(blob) for p in _GRADED_PATTERNS)


def collect_files(task_dir: Path, multistep: bool) -> tuple:
    """Return (file_records, verifier_texts).

    file_records: list of {group, label, path, content} for the modal viewer.
    verifier_texts: raw verifier sources (for graded/binary detection).
    """
    recs, verifiers = [], []

    def add(group, label, path: Path):
        content = read_file(path)
        recs.append({"group": group, "label": label,
                     "path": str(path.relative_to(REPO)), "content": content})
        return content

    # Environment (shared by single + multi step).
    dockerfile = task_dir / "environment" / "Dockerfile"
    if dockerfile.exists():
        add("env", "Dockerfile", dockerfile)

    if not multistep:
        inst = task_dir / "instruction.md"
        if inst.exists():
            add("instruction", "instruction.md", inst)
        for t in sorted((task_dir / "tests").glob("*")):
            if t.is_file():
                verifiers.append(add("verifier", f"verifier/{t.name}", t))
        for s in sorted((task_dir / "solution").glob("*")):
            if s.is_file():
                add("solution", f"solution/{s.name}", s)
    else:
        for step in sorted((task_dir / "steps").iterdir()):
            if not step.is_dir():
                continue
            sn = step.name
            inst = step / "instruction.md"
            if inst.exists():
                add("instruction", f"{sn}/instruction.md", inst)
            setup = step / "workdir" / "setup.sh"
            if setup.exists():
                add("setup", f"{sn}/workdir/setup.sh", setup)
            for t in sorted((step / "tests").glob("*")):
                if t.is_file():
                    verifiers.append(add("verifier", f"{sn}/verifier/{t.name}", t))
            for s in sorted((step / "solution").glob("*")):
                if s.is_file():
                    add("solution", f"{sn}/solution/{s.name}", s)
    return recs, verifiers


def step_snippets(task_dir: Path) -> list:
    """[(step_name, first ~160 chars of its instruction)] for multi-step cards."""
    out = []
    for step in sorted((task_dir / "steps").iterdir()):
        if not step.is_dir():
            continue
        inst = step / "instruction.md"
        snippet = ""
        if inst.exists():
            text = " ".join(inst.read_text(errors="replace").split())
            snippet = text[:160] + ("…" if len(text) > 160 else "")
        out.append((step.name, snippet))
    return out


def scan_tasks(weights: dict, focused: set) -> list:
    tasks = []
    tier_default, tier_overrides = load_validation()
    # Scan the live suite AND the archive (archived tasks are shown, flagged).
    roots = [(TASKS, False)]
    if ARCHIVE.is_dir():
        roots.append((ARCHIVE, True))
    for root, archived in roots:
        for cat_dir in sorted(root.iterdir()):
            if not cat_dir.is_dir() or cat_dir.name in SKIP_DIRS:
                continue
            for task_dir in sorted(cat_dir.iterdir()):
                toml_path = task_dir / "task.toml"
                if not (task_dir.is_dir() and toml_path.exists()):
                    continue
                try:
                    meta = tomllib.loads(toml_path.read_text())
                except Exception as e:
                    tasks.append({"_error": f"{task_dir.name}: {e}",
                                  "category": cat_dir.name, "name": task_dir.name,
                                  "archived": archived})
                    continue
                t = meta.get("task", {}) or {}
                md = meta.get("metadata", {}) or {}
                multistep = (task_dir / "steps").is_dir() or bool(meta.get("steps"))
                steps = step_snippets(task_dir) if multistep else []
                files, verifiers = collect_files(task_dir, multistep)
                tags = md.get("tags", []) or []
                tasks.append({
                    "dir": task_dir.name,
                    "category": md.get("category", cat_dir.name),
                    "name": t.get("name", task_dir.name),
                    "description": t.get("description", ""),
                    "difficulty": md.get("difficulty", "?"),
                    "shape": md.get("shape", ""),
                    "tags": tags,
                    "keywords": t.get("keywords", []) or [],
                    "multistep": multistep,
                    "n_steps": len(steps),
                    "steps": steps,
                    "reward_strategy": meta.get("multi_step_reward_strategy", ""),
                    "weight": weights.get(md.get("category", cat_dir.name), 1.0),
                    "graded": is_graded(verifiers),
                    "discriminating": "harness-discriminating" in tags,
                    "focused": task_dir.name in focused,
                    "status": md.get("status", "active"),
                    "deprecation_reason": md.get("deprecation_reason", ""),
                    "tier": ("retired" if (archived or md.get("status") == "deprecated")
                             else tier_overrides.get(task_dir.name, tier_default)),
                    "archived": archived,
                    "files": files,
                })
    return tasks


# ---------------------------------------------------------------- rendering

DIFF_ORDER = {"easy": 0, "medium": 1, "hard": 2, "?": 3}


def badge(text, cls="muted"):
    return f'<span class="badge {cls}">{escape(str(text))}</span>'


# Per-task WORK status — what's left to do on this task as a Task-Suite item.
# Derived from existing signals (heuristic, like the graded badge) unless the
# task.toml sets `[metadata] work_status = "..."` explicitly. Order = work queue
# priority. key -> (label, badge-class, meaning).
# Validation-ladder PROGRESS — show the highest tier each task has REACHED, not
# what it lacks. Tiers climb: todo → oracle → smoke → verdict. Source of truth:
# configs/validation-status.toml (operator-maintained: a `default` for all active
# tasks + per-task `[overrides]` as they advance). Mirrors RESULTS.md's ladder.
TIER_ORDER = ["todo", "oracle", "smoke", "verdict"]
TIER = {
    "todo":    ("to do",           "muted",   "Authored + offline grader tests. Not yet run end-to-end."),
    "oracle":  ("passes oracle ✓", "mid",     "Builds and the reference solve.sh scores 1.0 (Docker oracle, no LLM cost)."),
    "smoke":   ("e2e smoke ✓",     "ok",      "Both harnesses ran it end-to-end at n=1 — indicative separation captured."),
    "verdict": ("n≥3 verdict ✓",   "verdict", "Cleared the n≥3 pass^k reliability grid — banked into the comparison."),
    "retired": ("archived",        "retired", "Retired from the active suite; kept in archive/ for reference, out of the grid."),
}
TIER_RANK = {k: i for i, k in enumerate(TIER_ORDER)}


def load_validation() -> tuple:
    """(default_tier, {dir: tier}) from configs/validation-status.toml."""
    try:
        d = tomllib.loads((REPO / "configs" / "validation-status.toml").read_text())
        default = d.get("default", "todo")
        overrides = {k: v for k, v in (d.get("overrides") or {}).items()}
        return (default if default in TIER else "todo"), overrides
    except Exception:
        return "todo", {}


def tier_meta(t: dict) -> tuple:
    """Return (key, label, badge_class, meaning) for a task's ladder progress."""
    key = t.get("tier", "todo")
    if key not in TIER:
        key = "todo"
    label, cls, meaning = TIER[key]
    return key, label, cls, meaning


# ── Discrimination-design reference (moved off the roadmap) ───────────────────
# For the tasks built specifically to separate the HARNESS from the model: the
# four-part recipe + each task's trap / scoring / why-it's-the-harness. Rendered
# as a collapsible reference section at the bottom of the page. Task names track
# the on-disk dirs. Curated text — edit here and rerun.
TASK_EXPLAIN_INTRO = (
    "Every one of these tasks is built from the same four parts, so once you see the pattern you can read them all. "
    "<b>(1) A surface goal stated like a real user</b> — no hint of the trap, the hidden check, or the "
    "required strategy (“no telegraphing”). <b>(2) A hidden mechanism that makes the answer "
    "uncomputable without the harness</b>, enforced <i>mechanically</i> by a step's "
    "<span class='mono'>setup.sh</span> — it wipes all scratch before grading, silently rewrites a file, "
    "strips a value that was only ever spoken, or gates on latency. <b>(3) A graded scorer</b> "
    "(<span class='mono'>tests/test.sh</span>) — partial credit across weighted dimensions, never pass/fail "
    "(binary tasks saturate to 1.0 for two competent harnesses). <b>(4) The kill test</b> — if "
    "<span class='mono'>python3 -c</span> or one file-read could solve it, it measures the <i>model</i>; "
    "every task here defeats this. A <span class='mono'>0</span> on a <i>completed</i> run is VOID, not a "
    "loss — weight-0 <span class='mono'>diagnostics</span> tell the two apart."
)

TASK_EXPLAIN = [
    {"group": "Memory — state must survive a filesystem wipe, through the harness", "tests": [
        {"name": "distinguish-my-facts-from-others", "axis": "recall precision under distraction",
         "score": "correct / 12",
         "trap": "Learns 12 of Dana's facts, then 4 distractor turns inject confusable siblings (Sam's allergy, Jess's red Honda…); a recall step's setup.sh wipes all scratch + deletes /app before the recall, so answers must come from harness memory alone.",
         "scoring": "reward = correct / 12. A precise fact = 1.0; stating the distractor value or hedging both ≈ 0.33. Flat 0.0 if the wipe assertion fails (VOID).",
         "why": "No scratch survives between steps — only the harness's session memory does."},
        {"name": "persist-facts-through-corrections", "axis": "proactive memory update on correction",
         "score": "(correct/8) × (0.85+0.15·dinner)",
         "trap": "Mid-conversation the user CORRECTS two facts (timezone Pacific→Mountain, climbing nights Tue/Thu/Sat→Mon/Wed/Fri); the next step wipes scratch. Passive listening keeps the stale values.",
         "scoring": "reward = (correct_fields / 8) × (0.85 + 0.15·dinner_ok); the dinner plan must respect the CORRECTED constraints. Stale values score 0.",
         "why": "A model can't force the harness to write/update memory — without an UPDATE the old values survive the wipe."},
        {"name": "refresh-config-over-cached-value", "axis": "trust the live file over stale memory",
         "score": "1.0 iff 275 (not 45)",
         "trap": "Agent reads & repeatedly computes with cache_ttl_seconds: 45 (cementing it in memory); a later step's setup.sh SILENTLY rewrites the file to 275 (then deletes itself) and asks for the current value.",
         "scoring": "reward = 1.0 iff the answer is 275 AND not also 45 — dumping both forfeits it (an honest “275 (was 45)” is carved out).",
         "why": "The silent rewrite forces a choice between repeatedly-used memory (45) and a re-fetch (275); bare code never sees the change."},
    ]},
    {"group": "Long-context — retention as the window fills", "tests": [
        {"name": "track-final-state-through-corrections", "axis": "final-vs-stale value under window overflow",
         "score": "max(0, current−stale) / 12",
         "trap": "18 weekly reports (~1.3M tokens, >1× the 1M window); nearly every fact is corrected 2–3× over the quarter (lead Reyes→Tanaka→Okafor…). Reports deleted before recall.",
         "scoring": "reward = max(0, current_hits − stale_hits) / 12. Each fact: +1 for the FINAL value with ≤1 prior value present; −1 for adopting the GCP decoy. Dumping churned values = 0.",
         "why": "A script can't tell the final value from a stale one buried mid-context under saturation — it needs the harness to manage retention across 18 steps."},
        {"name": "chain-facts-across-survey-depth", "axis": "multi-hop lost-in-the-middle recall",
         "score": "matched / 8",
         "trap": "18 inspection records (~345K — FITS the window, so this tests retention not overflow) threaded into one growing conversation; 8 questions each chain two facts buried at different depths via a bridge entity.",
         "scoring": "reward = matched / 8; each needle must be positional + exclusive. Weight-0 early/middle/late fractions trace the rot curve.",
         "why": "Resolving a two-hop chain across facts at different conversational depths needs the harness's threaded context, not offline lookup."},
    ]},
    {"group": "Control loop + tool precision — recovery, replanning, selection", "tests": [
        {"name": "adaptive-tool-error-recovery", "axis": "adaptive error-recovery ladder",
         "score": "0.6·correct + 0.4·efficiency",
         "trap": "dfetch fails with 4 DIFFERENT actionable errors in sequence (bad-region→401→stale-lock→success); correct values are found only by exploring /app/dfetch.conf. Success emits an HMAC nonce whose secret lives in the stripped binary — forged answers fail --verify; the binary sha256 is pinned against swaps.",
         "scoring": "reward = 0.6·correctness + 0.4·efficiency, where efficiency = clamp((18−calls)/(18−3)). 1.0 = HMAC-verified files + an ordered progression log ending in “release”, ≤18 calls.",
         "why": "Each error demands interaction with live system state; there's no static answer, and only correct sequential calls unlock the secret."},
        {"name": "redesign-module-keep-constraints", "axis": "retain a bound across a mid-task context wipe",
         "score": "clamp 0.40 + fn 0.40 + cleanup 0.12 + replan 0.08",
         "trap": "A numeric clamp bound [−1000, 1000] is stated ONLY in conversation in steps 1–2; step 3's setup.sh strips the helper and the bound from disk + instructions, then asks for a refactor that must re-apply it. Leaked scratch notes → reward 0.0.",
         "scoring": "reward = clamp_memory 0.40 + functional 0.40 + cleanup 0.12 + replan 0.08. Without recalling the bound, the score caps ≈ 0.60.",
         "why": "The bound is unrecoverable from step 3's files/instructions — only harness-threaded conversation state unlocks the full score."},
        {"name": "pick-right-shell-utility", "axis": "tool selection among decoys",
         "score": "0.5·F1 + 0.5·efficiency",
         "trap": "60 tools, exactly 3 correct (opaque names — function only in --help); 9 name-collision decoys (count, analyze, rank) match the verbs but do the wrong thing. The answer VALUE is deliberately not scored (a script could compute it) — only logged tool invocations are.",
         "scoring": "reward = 0.5·selection_F1 + 0.5·call_efficiency. Computing offline without invoking tools = 0.0 (VOID).",
         "why": "Grading is purely on invocation discipline; a pure python3 solver scores 0."},
    ]},
    {"group": "Delegation + skill acquisition", "tests": [
        {"name": "parallel-delegation-under-deadline", "axis": "parallel sub-agent fan-out",
         "score": "correct / 60",
         "trap": "60 independent problems, each needing a value from a latency-gated binary (8s/call). Serial = 60×8s = 480s, blowing the 600s timeout even with instant math; only parallel sub-agent sessions clear enough in time.",
         "scoring": "reward = correct / 60. No concurrency bonus — a serial harness simply finishes fewer (mtime logs are advisory only).",
         "why": "A single synchronous token-stream hits a hard 480s floor; only independent parallel sessions beat the clock."},
        {"name": "skill-discovery-with-docs", "axis": "find the right skill by reading metadata",
         "score": "passed / 16",
         "trap": "13 skills; only tabular-shape-report is correct — and its name does NOT echo “shape”, while 3 better-named decoys emit near-miss output. The required --null=empty flag is documented only in the right SKILL.md. A SHA256 breadcrumb proves real discovery; running all 13 (brute sweep) trips a gate and denies credit.",
         "scoring": "reward = passed / 16 (8 files × {correct, discovered}). Near-miss = 1/2; swept = 0/2.",
         "why": "Discovery needs parsing structured tool metadata, not reasoning; the sweep gate + hash breadcrumb block reimplementation cheats."},
    ]},
    {"group": "Stateful workflow", "tests": [
        {"name": "clean-expense-ledger", "axis": "precise multi-axis ledger edit",
         "score": "per-decision / N",
         "trap": "A 340-row budget CSV; the agent must DISCOVER the dedup rule (identical date+vendor+amount+category) by inspection — never told. 6 May grocery dup-groups to remove, 7 lookalike groups (near-amounts 55.00/55.10, same-date-different-category…) to PRESERVE, plus a rent row to split 50/50. No answer key ever exists in the container.",
         "scoring": "reward = (dedup + preserve + rent_split + rent_orig_gone + collateral) / total, per decision — with a dedup gate that floors preserve/collateral at 0 if nothing was actually deduped (so “do nothing” can't score ≈0.5).",
         "why": "Requires empirically inferring the rule from the data, then a precise stateful transform — there's no key to learn from."},
    ]},
]


def render_task_explain() -> str:
    """The discrimination-design reference (moved off the roadmap): each
    harness-measuring task's trap / scoring / why, as a collapsible section."""
    blocks = []
    for grp in TASK_EXPLAIN:
        rows = []
        for t in grp["tests"]:
            rows.append(
                f'<details class="howrow"><summary>'
                f'<span class="howname">{escape(t["name"], quote=False)}</span> '
                f'<span class="howaxis">— {escape(t["axis"], quote=False)}</span>'
                f'<span class="howscore">{escape(t["score"], quote=False)}</span></summary>'
                f'<div class="howdet"><b>Trap:</b> {escape(t["trap"], quote=False)}<br>'
                f'<b>Scoring:</b> {escape(t["scoring"], quote=False)}<br>'
                f'<b>Harness-only:</b> {escape(t["why"], quote=False)}</div></details>'
            )
        blocks.append(
            f'<div class="howgrp"><h3>{escape(grp["group"], quote=False)}</h3>'
            f'{"".join(rows)}</div>'
        )
    return (
        '<div class="howsec">'
        '<h2>How these tasks measure the harness, not the model</h2>'
        f'<div class="howintro">{TASK_EXPLAIN_INTRO}</div>'
        f'{"".join(blocks)}'
        '</div>'
    )


def render(tasks: list, weights: dict) -> str:
    # Assign a global file index for the modal viewer.
    files_map = {}
    idx = 0
    for t in tasks:
        for f in t.get("files", []):
            f["_idx"] = idx
            files_map[idx] = {"name": f["label"], "path": f["path"],
                              "content": f["content"]}
            idx += 1

    files_js = json.dumps(files_map).replace("</", "<\\/")

    real = [t for t in tasks if "_error" not in t]
    n_total = len(real)
    n_cats = len({t["category"] for t in real})
    diff_hist = {}
    for t in real:
        diff_hist[t["difficulty"]] = diff_hist.get(t["difficulty"], 0) + 1
    n_multi = sum(1 for t in real if t["multistep"])
    n_graded = sum(1 for t in real if t["graded"])
    n_disc = sum(1 for t in real if t["discriminating"])
    n_focus = sum(1 for t in real if t["focused"])
    n_retired = sum(1 for t in real if t.get("status") == "deprecated")
    n_active = n_total - n_retired

    # Validation-ladder PROGRESS — cumulative: reaching a tier implies the ones
    # below it. Shows how far the suite has CLIMBED, not what it lacks.
    active = [t for t in real if not t.get("archived")]
    n_archived = n_total - len(active)

    def reached(tier):
        r = TIER_RANK[tier]
        return sum(1 for t in active if TIER_RANK.get(t.get("tier", "todo"), 0) >= r)
    n_oracle, n_smoke, n_verdict = reached("oracle"), reached("smoke"), reached("verdict")

    diff_bits = " · ".join(
        f"{k}: {diff_hist[k]}" for k in sorted(diff_hist, key=lambda d: DIFF_ORDER.get(d, 9))
    )

    summary = f"""
    <div class="summary">
      <div class="stat"><b>{n_active}</b><span>active tasks</span></div>
      <div class="stat work-done"><b>{n_oracle}</b><span>✓ passes oracle</span></div>
      <div class="stat work-done"><b>{n_smoke}</b><span>✓ e2e smoke</span></div>
      <div class="stat"><b>{n_verdict}</b><span>n≥3 verdict</span></div>
      <div class="stat"><b>{n_archived}</b><span>archived</span></div>
      <div class="stat"><b>{n_cats}</b><span>categories</span></div>
      <div class="stat wide"><b>difficulty</b><span>{escape(diff_bits)}</span></div>
    </div>"""

    tier_select = "".join(
        f'<option value="{k}">{TIER[k][0]}</option>' for k in (TIER_ORDER + ["retired"]))

    # Category sections, ordered by weight desc then name.
    cats = sorted({t["category"] for t in real},
                  key=lambda c: (-weights.get(c, 1.0), c))
    cat_select = "".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in cats)

    sections = []
    for cat in cats:
        ctasks = [t for t in real if t["category"] == cat]
        ctasks.sort(key=lambda t: (DIFF_ORDER.get(t["difficulty"], 9), t["dir"]))
        w = weights.get(cat, 1.0)
        wcls = "ok" if w >= 3.0 else ("mid" if w >= 1.5 else "bad")
        rows = "".join(render_card(t) for t in ctasks)
        sections.append(f"""
        <section class="catsec" data-cat="{escape(cat)}">
          <div class="cathead">
            <span class="catname">{escape(cat)}</span>
            <span class="badge {wcls}">weight {w:g}</span>
            <span class="muted">{len(ctasks)} task{'s' if len(ctasks) != 1 else ''}</span>
          </div>
          <div class="acc-list">{rows}</div>
        </section>""")

    errs = [t for t in tasks if "_error" in t]
    err_html = ""
    if errs:
        err_html = '<div class="err">task.toml parse errors:\n' + "\n".join(
            escape(e["_error"]) for e in errs) + "</div>"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return PAGE.format(summary=summary, sections="".join(sections),
                       howtests=render_task_explain(),
                       cat_select=cat_select, tier_select=tier_select,
                       files_js=files_js, ts=ts,
                       err_html=err_html, n_total=n_total,
                       n_active=n_active, n_archived=n_archived)


def render_card(t: dict) -> str:
    """Render one task as an accordion row: a collapsed header (name + status
    badges) that expands to the full detail (description, steps, tags, files)."""
    diff = t["difficulty"]
    dcls = {"easy": "ok", "medium": "mid", "hard": "bad"}.get(diff, "muted")
    grade_badge = (badge("graded", "ok") if t["graded"]
                   else badge("binary", "bad"))
    retired = t.get("status") == "deprecated"
    wkey, wlabel, wcls, wmeaning = tier_meta(t)
    archived = t.get("archived", False)

    # (Archived tasks are flagged by their tier badge = "archived"; no separate flag.)
    # progress tier badge, then difficulty/grading/flags (in the body).
    head_badges = [badge(wlabel, wcls)]
    flags = []
    if t["focused"]:
        flags.append(badge("focused n=5", "focus"))
    flags.append(badge(f"{t['n_steps']} steps", "step") if t["multistep"]
                 else badge("1 step", "muted"))

    # File chips grouped by kind.
    chip_groups = [("instruction", "instruction"), ("setup", "setup"),
                   ("verifier", "verifier"), ("solution", "solution"),
                   ("env", "env")]
    chips = []
    for group, cls in chip_groups:
        for f in t["files"]:
            if f["group"] == group:
                chips.append(
                    f'<span class="chip {cls}" onclick="showFile({f["_idx"]})" '
                    f'title="{escape(f["path"])}">{escape(f["label"])}</span>')
    chips_html = "".join(chips) or '<span class="muted">no files</span>'

    steps_html = ""
    if t["steps"]:
        rows = "".join(
            f'<div class="steprow"><span class="stepname">{escape(sn)}</span>'
            f'<span class="muted">{escape(snip)}</span></div>'
            for sn, snip in t["steps"])
        steps_html = f'<div class="steps">{rows}</div>'

    tags_html = "".join(f'<span class="tag">{escape(x)}</span>'
                        for x in t["tags"] if "discriminat" not in x.lower())

    # data-* attributes drive client-side filtering.
    data = (f'data-cat="{escape(t["category"])}" data-diff="{escape(diff)}" '
            f'data-graded="{int(t["graded"])}" data-disc="{int(t["discriminating"])}" '
            f'data-focus="{int(t["focused"])}" data-multi="{int(t["multistep"])}" '
            f'data-status="{"retired" if retired else "active"}" data-tier="{wkey}" '
            f'data-archived="{int(archived)}" '
            f'data-search="{escape((t["name"] + " " + t["dir"] + " " + t["shape"] + " " + t["description"] + " " + " ".join(t["tags"])).lower())}"')

    retired_banner = ""
    if retired:
        where = "ARCHIVED" if archived else "RETIRED"
        retired_banner = (f'<div class="retired-note"><b>{where} (out of the active suite — not deleted; in archive/).</b> '
                          f'{escape(t["deprecation_reason"] or "Excluded from the harness-discrimination grid; kept for reference.")}</div>')

    return f"""
    <div class="task{' task-retired' if retired else ''}" {data}>
      <div class="acc-head" onclick="toggleAcc(this)">
        <span class="caret">▶</span>
        <span class="tname">{escape(t["dir"])}</span>
        {"".join(head_badges)}
      </div>
      <div class="acc-body">
        <div class="badges"><span class="badge {dcls}">{escape(diff)}</span> {grade_badge} {"".join(flags)}</div>
        <div class="work-note"><b>Status:</b> {escape(wmeaning)}</div>
        {retired_banner}
        <div class="meta">
          <span class="mono muted">{escape(t["name"])}</span>
          <span class="shape">shape: {escape(t["shape"] or "—")}</span>
        </div>
        <div class="desc">{escape(t["description"])}</div>
        {steps_html}
        <div class="tags">{tags_html}</div>
        <div class="sec">Files <span class="muted">(click to view)</span></div>
        <div class="chips">{chips_html}</div>
      </div>
    </div>"""


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Task Suite</title>
<style>
  body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#0f1117;color:#e6e6e6;padding:24px}}
  a{{color:#9db4d6}}
  .nav{{display:flex;gap:10px;align-items:center;margin-bottom:14px}}
  .nav a{{font-size:13px;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:4px 12px;color:#9db4d6}}
  .nav a:hover{{background:#1c2331}}
  .nav a.active{{background:#1b2a1f;border-color:#3a5a44;color:#9fe0a5;font-weight:600}}
  h1{{font-size:18px;margin:0 0 2px}} .ts{{color:#8a8f98;font-size:12px;margin-bottom:16px}}
  .summary{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px;max-width:1200px}}
  .stat{{background:#171a22;border:1px solid #262b36;border-radius:10px;padding:10px 16px;min-width:84px}}
  .stat b{{display:block;font-size:20px;color:#e6e6e6}} .stat span{{font-size:11px;color:#8a8f98;text-transform:uppercase;letter-spacing:.4px}}
  .stat.wide{{min-width:180px}} .stat.wide b{{font-size:13px}}
  .filterbar{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:18px;max-width:1200px;
    background:#171a22;border:1px solid #262b36;border-radius:10px;padding:12px 14px}}
  .filterbar select,.filterbar input{{background:#10131a;color:#e6e6e6;border:1px solid #2f3645;border-radius:6px;padding:5px 9px;font-size:13px}}
  .filterbar label{{font-size:12px;color:#8a8f98;display:flex;gap:5px;align-items:center;cursor:pointer}}
  .filterbar input[type=search]{{min-width:220px}}
  .filterbar .count{{margin-left:auto;color:#8a8f98;font-size:12px}}
  .catsec{{max-width:1200px;margin-bottom:26px}}
  .cathead{{display:flex;gap:10px;align-items:center;margin-bottom:10px;border-bottom:1px solid #262b36;padding-bottom:6px}}
  .catname{{font-size:15px;font-weight:700;text-transform:capitalize}}
  .acc-list{{display:flex;flex-direction:column;gap:6px}}
  .task{{background:#171a22;border:1px solid #262b36;border-radius:9px;overflow:hidden}}
  .acc-head{{display:flex;gap:7px;align-items:center;flex-wrap:wrap;padding:9px 12px;cursor:pointer}}
  .acc-head:hover{{background:#1c2129}}
  .caret{{color:#717a88;font-size:10px;transition:transform .12s;flex-shrink:0}}
  .task.open .caret{{transform:rotate(90deg)}}
  .acc-body{{display:none;padding:2px 14px 13px 14px;border-top:1px solid #20242e}}
  .task.open .acc-body{{display:block}}
  .acc-body .badges{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 0}}
  .work-note{{font-size:12px;color:#c4ccd8;background:#10131a;border:1px solid #222734;border-radius:6px;padding:7px 10px;margin:10px 0 8px}}
  .tname{{font-size:13.5px;font-weight:700;margin-right:auto;font-family:ui-monospace,Menlo,monospace}}
  .meta{{display:flex;flex-wrap:wrap;gap:10px;font-size:11px;margin-bottom:8px}}
  .shape{{color:#9db4d6}}
  .desc{{font-size:12.5px;color:#cdd6e4;margin-bottom:8px}}
  .steps{{border-top:1px dashed #262b36;border-bottom:1px dashed #262b36;padding:6px 0;margin-bottom:8px;max-height:148px;overflow:auto}}
  .steprow{{display:flex;gap:8px;font-size:11px;padding:1px 0}}
  .stepname{{color:#bfe3c5;font-family:ui-monospace,Menlo,monospace;min-width:104px;flex-shrink:0}}
  .tags{{margin-bottom:8px}}
  .tag{{display:inline-block;background:#1a1c22;border:1px solid #262b36;border-radius:5px;padding:0 6px;margin:2px 3px 0 0;font-size:10.5px;color:#8a8f98}}
  .sec{{color:#8a8f98;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin:4px 0 6px;border-top:1px solid #262b36;padding-top:7px}}
  .chips{{margin-top:6px}}
  .chip{{display:inline-block;border:1px solid #2f3645;border-radius:6px;padding:1px 7px;margin:2px;font-size:11.5px;cursor:pointer;background:#222734}}
  .chip:hover{{filter:brightness(1.25)}}
  .chip.instruction{{background:#1c2331;color:#9db4d6}}
  .chip.verifier{{background:#2a1f25;color:#e69ab8;border-color:#5a2a3d}}
  .chip.solution{{background:#1b2a1f;color:#9fe0a5;border-color:#3a5a44}}
  .chip.env{{background:#2a2519;color:#e6c98a;border-color:#5a4a2a}}
  .chip.setup{{background:#241f2a;color:#c39ae6;border-color:#4a2a5a}}
  .muted{{color:#8a8f98}} .mono{{font-family:ui-monospace,Menlo,monospace}}
  .badge{{padding:1px 7px;border-radius:6px;font-size:11px;font-weight:600}}
  .badge.ok{{background:#163a22;color:#5fd07e}} .badge.bad{{background:#3a1616;color:#ef7a7a}}
  .badge.mid{{background:#3a2f16;color:#e6c98a}} .badge.muted{{background:#222734;color:#9aa1ad}}
  .badge.disc{{background:#2a1f3a;color:#c39ae6}} .badge.focus{{background:#16303a;color:#5fd0d0}}
  .badge.step{{background:#1c2331;color:#9db4d6}}
  .badge.retired{{background:#4a1010;color:#ff9b9b;border:1px solid #7a2222}}
  .badge.verdict{{background:#13502b;color:#7fe6a0;border:1px solid #2f7a4a;font-weight:700}}
  .badge.review{{background:#3a2a10;color:#f0b860;border:1px solid #6a4a18}}
  .badge.approved{{background:#163a22;color:#5fd07e;border:1px solid #2f5238}}
  .task-retired{{opacity:.66;border-color:#5a2020;background:#1a1212}}
  .task-retired:hover{{opacity:1}}
  .stat.work-done b{{color:#5fd07e}} .stat.work-todo b{{color:#e6c98a}}
  .toolbtn{{background:#10131a;color:#9db4d6;border:1px solid #2f3645;border-radius:6px;padding:5px 10px;font-size:12px;cursor:pointer}}
  .toolbtn:hover{{background:#1c2331}}
  .retired-note{{background:#2a1414;border:1px solid #5a2020;color:#f0a8a8;border-radius:6px;padding:7px 9px;margin:6px 0;font-size:12px;line-height:1.4}}
  .err{{background:#3a1616;color:#ef7a7a;padding:8px;border-radius:6px;margin-bottom:12px;max-width:1200px;white-space:pre-wrap;font-size:12px}}
  .hidden{{display:none!important}}
  /* discrimination-design reference (bottom of page) */
  .howsec{{max-width:1200px;margin:36px 0 24px;border-top:1px solid #262b36;padding-top:18px}}
  .howsec h2{{font-size:16px;font-weight:700;color:#cdd6e4;margin:0 0 4px}}
  .howintro{{font-size:12.5px;line-height:1.6;color:#cdd6e4;background:#13182098;border:1px solid #2a3550;
    border-left:3px solid #5fd0d0;border-radius:10px;padding:12px 16px;margin:8px 0 16px}}
  .howgrp{{margin-bottom:14px}}
  .howgrp h3{{font-size:13px;font-weight:700;color:#cdd6e4;margin:0 0 6px}}
  details.howrow{{background:#171a22;border:1px solid #262b36;border-radius:8px;margin-bottom:6px}}
  details.howrow summary{{cursor:pointer;padding:9px 12px;font-size:13px;display:flex;gap:9px;
    align-items:baseline;list-style:none}}
  details.howrow summary::-webkit-details-marker{{display:none}}
  details.howrow summary::before{{content:'\\25B6';color:#717a88;font-size:9px;flex-shrink:0}}
  details.howrow[open] summary::before{{content:'\\25BC'}}
  .howname{{font-family:ui-monospace,Menlo,monospace;font-weight:700;color:#e6e6e6}}
  .howaxis{{color:#9aa1ad}}
  .howscore{{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:11px;color:#717a88;white-space:nowrap}}
  .howdet{{padding:2px 14px 12px;font-size:12.5px;line-height:1.6;color:#c4ccd8;border-top:1px solid #20242e}}
  /* modal (shared with agent-status) */
  #ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:50}}
  #mo{{display:none;position:fixed;top:5%;left:50%;transform:translateX(-50%);width:min(900px,92vw);max-height:88vh;
       background:#10131a;border:1px solid #2f3645;border-radius:10px;flex-direction:column;z-index:51}}
  #mo header{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid #262b36}}
  #mo h3{{margin:0;font:13px monospace}} #mo .x{{cursor:pointer;color:#8a8f98;font-size:20px;line-height:1}}
  #mo .path{{color:#6b7280;font:11px monospace;padding:0 16px 10px}}
  #mo pre{{margin:0;padding:16px;overflow:auto;white-space:pre-wrap;word-break:break-word;font:12.5px/1.55 ui-monospace,Menlo,monospace;color:#cdd6e4}}
</style></head><body>
<div class="nav">
  <a href="agent-status.html">Agent status</a>
  <a href="task-catalog.html" class="active">Task Suite</a>
  <a href="roadmap.html">Roadmap</a>
</div>
<h1>Task Suite — every eval task (live + archived)</h1>
<div class="ts">generated {ts} · source: tasks/ + archive/ + configs/ · re-run tools/task_catalog.py to refresh ·
  click a row to expand: what it asks, how it's graded, the oracle, the environment, and the work left to do<br>
  <b>{n_active}</b> live tasks + <b>{n_archived}</b> archived (retired from the active suite, kept in <span class="mono">archive/</span> for reference — flagged, not deleted)</div>
{err_html}
{summary}
<div class="filterbar">
  <select id="f-archived"><option value="">live + archived</option><option value="0">live only</option><option value="1">archived only</option></select>
  <select id="f-cat"><option value="">all categories</option>{cat_select}</select>
  <select id="f-tier"><option value="">any progress</option>{tier_select}</select>
  <select id="f-diff"><option value="">any difficulty</option>
    <option value="easy">easy</option><option value="medium">medium</option><option value="hard">hard</option></select>
  <label><input type="checkbox" id="f-graded"> graded only</label>
  <label><input type="checkbox" id="f-focus"> focused set</label>
  <label><input type="checkbox" id="f-multi"> multi-step</label>
  <input type="search" id="f-search" placeholder="search name / shape / description / tags">
  <button class="toolbtn" onclick="expandAll(1)">expand all</button>
  <button class="toolbtn" onclick="expandAll(0)">collapse all</button>
  <span class="count" id="count"></span>
</div>
{sections}
{howtests}

<div id="ov" onclick="hideFile()"></div>
<div id="mo">
  <header><h3 id="mo-name"></h3><span class="x" onclick="hideFile()">&times;</span></header>
  <div class="path" id="mo-path"></div>
  <pre id="mo-body"></pre>
</div>
<script>
const FILES = {files_js};
const TOTAL = {n_total};
function showFile(i){{
  const f = FILES[i]; if(!f) return;
  document.getElementById('mo-name').textContent = f.name;
  document.getElementById('mo-path').textContent = f.path;
  document.getElementById('mo-body').textContent = f.content;
  document.getElementById('ov').style.display='block';
  document.getElementById('mo').style.display='flex';
}}
function hideFile(){{
  document.getElementById('ov').style.display='none';
  document.getElementById('mo').style.display='none';
}}
document.addEventListener('keydown', e=>{{ if(e.key==='Escape') hideFile(); }});

function toggleAcc(head){{ head.parentElement.classList.toggle('open'); }}
function expandAll(on){{
  document.querySelectorAll('.task').forEach(t=>{{
    if(t.classList.contains('hidden')) return;
    t.classList.toggle('open', !!on);
  }});
}}

const F = id => document.getElementById(id);
function applyFilters(){{
  const cat=F('f-cat').value, tier=F('f-tier').value, diff=F('f-diff').value,
        arch=F('f-archived').value,
        graded=F('f-graded').checked,
        focus=F('f-focus').checked, multi=F('f-multi').checked,
        q=F('f-search').value.trim().toLowerCase();
  let shown=0;
  document.querySelectorAll('.task').forEach(c=>{{
    let ok=true;
    if(arch && c.dataset.archived!==arch) ok=false;
    if(cat && c.dataset.cat!==cat) ok=false;
    if(tier && c.dataset.tier!==tier) ok=false;
    if(diff && c.dataset.diff!==diff) ok=false;
    if(graded && c.dataset.graded!=='1') ok=false;
    if(focus && c.dataset.focus!=='1') ok=false;
    if(multi && c.dataset.multi!=='1') ok=false;
    if(q && !c.dataset.search.includes(q)) ok=false;
    c.classList.toggle('hidden', !ok);
    if(ok) shown++;
  }});
  // hide category sections with no visible tasks
  document.querySelectorAll('.catsec').forEach(s=>{{
    const any=[...s.querySelectorAll('.task')].some(c=>!c.classList.contains('hidden'));
    s.classList.toggle('hidden', !any);
  }});
  F('count').textContent = shown+' / '+TOTAL+' shown';
}}
['f-archived','f-cat','f-tier','f-diff','f-graded','f-focus','f-multi','f-search'].forEach(
  id=>{{const el=F(id); el.addEventListener('input',applyFilters); el.addEventListener('change',applyFilters);}});
applyFilters();
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open in browser after writing")
    args = ap.parse_args()

    weights = load_weights()
    focused = load_focused_names()
    tasks = scan_tasks(weights, focused)
    OUT.write_text(render(tasks, weights))
    n = len([t for t in tasks if "_error" not in t])
    print(f"wrote {OUT} ({n} tasks)")
    if args.open:
        webbrowser.open(f"file://{OUT}")


if __name__ == "__main__":
    main()
