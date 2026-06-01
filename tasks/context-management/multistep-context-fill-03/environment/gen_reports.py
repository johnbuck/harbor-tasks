#!/usr/bin/env python3
"""Generate 18 weekly reports covering TWO parallel projects: ORION + LYRA.

CONTEXT-SATURATION ladder rung 3 of 3 = CROSS-TALK PRECISION. Same 1M-window
overflow (~72K tokens/report, ~1.3M cumulative), but the stressor is ATTRIBUTION
under interleaving: every report discusses both PROJECT ORION (a satellite
ground-network programme) and PROJECT LYRA (a datacenter platform), each with a
parallel set of attributes (lead, budget, site, vendor, headcount, go-live). The
values are stable but CONFUSABLE across the two projects, and re-stated several
times so both are in-window. The failure mode is cross-attribution -- reporting
Lyra's lead as Orion's, etc. -- which heavy interleaving across a full window
provokes.

Scoring (steps/19-recall/tests/test.sh) is line-anchored per (project,attribute):
+1 for the correct value on that slot's line, -1 if the SIBLING project's value
appears there (cross-attribution). One DRAFT "Project Nova" decoy must not appear.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

TITLE = "PORTFOLIO REVIEW - PROJECTS ORION & LYRA - WEEKLY STATUS"
LINES_PER_SECTION = 300

SECTIONS = [
    ("1. LEADERSHIP & STAFFING", "staffing"),
    ("2. BUDGET & FINANCE", "budget"),
    ("3. SITES & FACILITIES", "sites"),
    ("4. VENDORS & PARTNERS", "vendors"),
    ("5. HEADCOUNT & RESOURCING", "headcount"),
    ("6. SCHEDULE & GO-LIVE", "schedule"),
    ("7. ENGINEERING NOTES", "engineering"),
    ("8. ACTION ITEMS & NOTES", "actions"),
]

SUBSYSTEMS = [
    "the uplink array", "the database cluster", "the antenna positioner",
    "the load balancer", "the telemetry router", "the message bus",
    "the ground modem bank", "the object store", "the timing reference",
    "the service mesh", "the power bus", "the backup pipeline",
]
TEAMS = [
    "the systems team", "the platform team", "the integration cell",
    "the reliability office", "the operations desk", "the QA cell",
    "the architecture board", "the security group",
]
VERBS = ["reviewed", "rebaselined", "regression-tested", "profiled", "validated",
         "audited", "benchmarked", "stress-tested"]
METRICS = ["link margin", "p99 latency", "throughput", "pointing error",
           "replication lag", "duty cycle", "failover time"]
OUTCOMES = ["within tolerance", "nominal against the baseline", "trending favourably",
            "flagged for a follow-up cycle", "carried into next week's agenda",
            "closed with no further action"]


def filler_line(section, wk, idx):
    proj = "Orion" if (idx % 2 == 0) else "Lyra"
    sub = SUBSYSTEMS[(wk * 7 + idx) % len(SUBSYSTEMS)]
    team = TEAMS[(wk * 3 + idx) % len(TEAMS)]
    verb = VERBS[(wk + idx) % len(VERBS)]
    metric = METRICS[(wk * 5 + idx) % len(METRICS)]
    out = OUTCOMES[(wk * 2 + idx) % len(OUTCOMES)]
    return (f"[{proj}] item {section[:3].upper()}-{wk:02d}{idx:03d}: {team} {verb} "
            f"{sub}; measured {metric} was {out}.")


# Both projects' attributes, re-stated across several weeks (stable, confusable).
def pair(attr, orion, lyra):
    return [("__O__", f"Project Orion - {attr}: {orion}."),
            ("__L__", f"Project Lyra - {attr}: {lyra}.")]


SCHED = {
    "staffing": [(1, "engineering lead", "Dr. Elena Marsh", "Dr. Victor Crane"),
                 (7, "engineering lead", "Dr. Elena Marsh", "Dr. Victor Crane"),
                 (13, "engineering lead", "Dr. Elena Marsh", "Dr. Victor Crane")],
    "budget":   [(2, "approved budget", "$7.4M", "$3.6M"),
                 (9, "approved budget", "$7.4M", "$3.6M"),
                 (15, "approved budget", "$7.4M", "$3.6M")],
    "sites":    [(3, "primary site", "Site K9", "Frankfurt"),
                 (10, "primary site", "Site K9", "Frankfurt"),
                 (16, "primary site", "Site K9", "Frankfurt")],
    "vendors":  [(4, "prime vendor", "Heliosat", "Brightlink"),
                 (11, "prime vendor", "Heliosat", "Brightlink"),
                 (17, "prime vendor", "Heliosat", "Brightlink")],
    "headcount":[(5, "headcount", "38 engineers", "52 engineers"),
                 (8, "headcount", "38 engineers", "52 engineers"),
                 (12, "headcount", "38 engineers", "52 engineers")],
    "schedule": [(6, "go-live target", "2027-Q2", "2026-Q4"),
                 (14, "go-live target", "2027-Q2", "2026-Q4")],
}

# week -> list of (section_key, sentence)
INJECTIONS = {}
for sec, rows in SCHED.items():
    for (wk, attr, orion, lyra) in rows:
        INJECTIONS.setdefault(wk, [])
        INJECTIONS[wk].append((sec, f"Project Orion - {attr}: {orion}."))
        INJECTIONS[wk].append((sec, f"Project Lyra - {attr}: {lyra}."))
# DRAFT decoy: a third project that must never be reported
INJECTIONS.setdefault(16, []).append(
    ("actions", "DRAFT - NOT APPROVED: a speculative Project Nova (lead Dr. Quill, "
                "budget $9.9M, site Reykjavik) is under discussion only and is not "
                "part of the portfolio of record; do not report it."))


def build_section(title, key, wk):
    lines = [title, "-" * len(title)]
    injected = [s for (k, s) in INJECTIONS.get(wk, []) if k == key]
    spots = sorted({(wk * 31 + i * 89) % LINES_PER_SECTION for i in range(len(injected))})
    spot_set = set(spots)
    inj_iter = iter(injected)
    for i in range(LINES_PER_SECTION):
        if i in spot_set:
            try:
                lines.append("    " + next(inj_iter))
            except StopIteration:
                pass
        lines.append(filler_line(key, wk, i))
    for s in inj_iter:
        lines.append("    " + s)
    lines.append("")
    return lines


total_chars = 0
for wk in range(1, 19):
    body = [
        TITLE,
        f"WEEK {wk:02d} OF 18",
        "=" * 60,
        "",
        "This portfolio report covers two parallel programmes, PROJECT ORION (a",
        "satellite ground-network rollout) and PROJECT LYRA (a datacenter platform).",
        "Each project's facts are reported separately; keep each project's values",
        "attributed to the correct project.",
        "",
    ]
    for title, key in SECTIONS:
        body.extend(build_section(title, key, wk))
    text = "\n".join(body) + "\n"
    total_chars += len(text)
    with open(os.path.join(OUT_DIR, f"week_{wk:02d}.txt"), "w") as fh:
        fh.write(text)

est_tokens = total_chars / 4
print(f"ORION/LYRA: 18 reports, {total_chars} chars, ~{est_tokens:.0f} est tokens "
      f"(~{est_tokens/18:.0f}/report); window target 1,048,576")
