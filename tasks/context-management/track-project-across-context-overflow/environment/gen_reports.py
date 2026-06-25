#!/usr/bin/env python3
"""Generate 18 weekly status reports for PROJECT HELIOS.

This is a CONTEXT-WINDOW-SATURATION test, not a needle-in-filler test. The
target model (deepseek-v4-pro) has a 1,048,576-token window, so the 18 reports
are sized to ~58K tokens each (~1.05M cumulative) so that the window OVERFLOWS
before the final recall step. The content is plausible, meaningful, evolving
project prose (no "this is filler, ignore it" framing) -- the analyst must
actually read it and track state.

Two fact classes are planted deliberately:
  * STABLE-EARLY facts (kickoff, site, integrator, software) are stated once in
    weeks 1-8 and never repeated -> evicted from a raw window by recall time, so
    only a harness that externalises to memory recalls them.
  * UPDATE-TRAP facts (lead, launch, budget, satellites, ops-center, coolant,
    retention, vendor) are introduced early then CORRECTED in a late week ->
    probes stale-value surfacing (report the latest, never the superseded value).
  * One DRAFT decoy (an unapproved launch slip) must never be reported.

Canonical answers + stale/decoy penalties live in steps/19-recall/tests/test.sh.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

PROJECT = "PROJECT HELIOS"
SUBTITLE = "GROUND-STATION NETWORK ROLLOUT - WEEKLY ENGINEERING REVIEW"

# Each report targets ~72K tokens (~290K chars). Total ~1.3M tokens across 18
# reports = ~1.25x the 1,048,576 window, so it overflows with margin and early
# reports are evicted before recall. ~300 lines/section x 8 sections.
LINES_PER_SECTION = 300

SECTIONS = [
    ("1. SCHEDULE & MILESTONES", "schedule"),
    ("2. STAFFING & ORGANIZATION", "staffing"),
    ("3. PROCUREMENT & VENDORS", "procurement"),
    ("4. ENGINEERING & SUBSYSTEMS", "engineering"),
    ("5. BUDGET & FINANCE", "budget"),
    ("6. RISK & COMPLIANCE", "compliance"),
    ("7. TEST CAMPAIGN", "testing"),
    ("8. ACTION ITEMS & NOTES", "actions"),
]

SUBSYSTEMS = [
    "the uplink array", "the downlink chain", "the timing reference", "the power bus",
    "the thermal loop", "the attitude-control stack", "the telemetry router",
    "the command queue", "the ground modem bank", "the antenna positioner",
    "the fault-management layer", "the data-archival tier", "the security gateway",
    "the weather-feed ingestor", "the orbit-propagation service",
]
TEAMS = [
    "the avionics team", "the ground-software team", "the integration cell",
    "the RF group", "the reliability office", "the operations desk",
    "the supply-chain group", "the systems-engineering board", "the QA cell",
]
VERBS = [
    "reviewed", "rebaselined", "regression-tested", "profiled", "instrumented",
    "load-tested", "re-validated", "audited", "characterised", "stress-tested",
]
METRICS = [
    "link margin", "bit-error rate", "acquisition latency", "thermal headroom",
    "command round-trip time", "pointing error", "duty cycle", "packet-loss rate",
]
OUTCOMES = [
    "within tolerance", "nominal against the baseline", "trending favourably",
    "flagged for a follow-up cycle", "carried into next week's agenda",
    "closed with no further action", "escalated to the engineering board",
]


def filler_line(section, wk, idx):
    """One plausible status-report sentence, deterministic per (section,wk,idx)."""
    sub = SUBSYSTEMS[(wk * 7 + idx) % len(SUBSYSTEMS)]
    team = TEAMS[(wk * 3 + idx) % len(TEAMS)]
    verb = VERBS[(wk + idx) % len(VERBS)]
    metric = METRICS[(wk * 5 + idx) % len(METRICS)]
    out = OUTCOMES[(wk * 2 + idx) % len(OUTCOMES)]
    forms = {
        "schedule": f"Milestone S-{wk:02d}{idx:03d}: {team} {verb} {sub}; the {metric} was {out}.",
        "staffing": f"{team} reported {sub} staffing at planned levels; ramp item {wk:02d}{idx:03d} stays {out}.",
        "procurement": f"Procurement line P-{wk:02d}{idx:03d} covering {sub} was {verb} and is {out}.",
        "engineering": f"Engineering note E-{wk:02d}{idx:03d}: {sub} was {verb} by {team}; {metric} {out}.",
        "budget": f"Cost line B-{wk:02d}{idx:03d} for {sub} was {verb}; spend variance {out}.",
        "compliance": f"Risk item R-{wk:02d}{idx:03d} on {sub} was {verb} by {team} and is {out}.",
        "testing": f"Test run T-{wk:02d}{idx:03d}: {team} {verb} {sub}; measured {metric} was {out}.",
        "actions": f"Action A-{wk:02d}{idx:03d}: {team} to follow up on {sub}; status {out}.",
    }
    return forms[section]


# week -> list of (section_key, sentence). Load-bearing facts the analyst tracks.
INJECTIONS = {
    1: [
        ("schedule", "The program kickoff was formally recorded on 2026-03-15 and is the baseline date of record."),
        ("staffing", "Project lead: Dr. Helena Vance, who chairs this weekly review."),
        ("schedule", "The launch window is currently targeted for 2027-Q3."),
        ("engineering", "The baseline constellation comprises 6 satellites."),
    ],
    2: [("budget", "The approved program budget stands at $4.2M for the fiscal year.")],
    3: [
        ("staffing", "Operations are coordinated from the Denver operations center."),
        ("procurement", "Antenna vendor evaluation opened; Aterna submitted the first bid."),
    ],
    4: [("engineering", "The primary ground station site is confirmed as Site B12.")],
    5: [
        ("procurement", "Brightpath entered the antenna vendor evaluation as a second candidate."),
        ("staffing", "Northwind Systems is confirmed as the systems integration partner."),
    ],
    6: [("engineering", "Thermal design specifies coolant type R-410A for the equipment shelters.")],
    7: [
        ("procurement", "Cardinal joined the antenna vendor shortlist as a third candidate."),
        ("compliance", "Data retention policy is set at 12 years for mission telemetry."),
    ],
    8: [("engineering", "The ground software baseline is locked at OrbitOS 3.1.")],
    9: [("staffing", "Following a program reorganization, Dr. Samuel Okonkwo assumes the project lead role from Dr. Vance, effective immediately.")],
    10: [("engineering", "A scope review reduced the constellation from 6 satellites to 4 satellites.")],
    11: [
        ("procurement", "Antenna vendor decision: Brightpath is selected as the awarded vendor."),
        ("staffing", "The operations center is relocating from Denver to Phoenix."),
    ],
    12: [("budget", "The program budget was raised from $4.2M to $5.1M following the scope change.")],
    13: [("procurement", "Brightpath failed its supplier audit and is disqualified; the contract reverts to Cardinal as the awarded vendor.")],
    14: [("schedule", "CORRECTION: the launch window was misstated earlier; the approved window is 2027-Q4 (this supersedes 2027-Q3).")],
    15: [("engineering", "CORRECTION: the coolant specification is updated from R-410A to R-32 per the revised thermal analysis.")],
    16: [("compliance", "DRAFT - NOT APPROVED: a proposal to slip the launch to 2028-Q1 is under discussion only and must not be treated as the plan of record.")],
    17: [("compliance", "Compliance update: the data retention period is reduced from 12 years to 7 years.")],
    18: [("actions", "Closeout week: no new baseline changes; all prior decisions of record stand as last stated.")],
}


def build_section(title, key, wk):
    lines = [title, "-" * len(title)]
    injected = [s for (k, s) in INJECTIONS.get(wk, []) if k == key]
    spots = sorted({(wk * 31 + i * 137) % LINES_PER_SECTION for i in range(len(injected))})
    spot_to_inj = {sp: n for n, sp in enumerate(spots)}
    inj_iter = iter(injected)
    placed = 0
    for i in range(LINES_PER_SECTION):
        if i in spot_to_inj:
            try:
                lines.append("    " + next(inj_iter))
                placed += 1
            except StopIteration:
                pass
        lines.append(filler_line(key, wk, i))
    for s in inj_iter:  # safety: place any leftover
        lines.append("    " + s)
    lines.append("")
    return lines


total_chars = 0
for wk in range(1, 19):
    body = [
        f"{PROJECT} - {SUBTITLE}",
        f"WEEK {wk:02d} OF 18",
        "=" * 60,
        "",
        "This report records the project state for the week. Facts are introduced,",
        "updated, and occasionally corrected from week to week; the values below are",
        "the current state as of this report unless a later report supersedes them.",
        "",
    ]
    for title, key in SECTIONS:
        body.extend(build_section(title, key, wk))
    text = "\n".join(body) + "\n"
    total_chars += len(text)
    with open(os.path.join(OUT_DIR, f"week_{wk:02d}.txt"), "w") as fh:
        fh.write(text)

est_tokens = total_chars / 4
print(f"generated 18 weekly reports: {total_chars} chars, ~{est_tokens:.0f} est tokens "
      f"(~{est_tokens/18:.0f}/report); window target 1,048,576")
