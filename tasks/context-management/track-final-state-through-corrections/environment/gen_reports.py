#!/usr/bin/env python3
"""Generate 18 weekly status reports for PROJECT VEGA (datacenter migration).

CONTEXT-SATURATION ladder rung 2 of 3 = UPDATE-CHURN. The stressor is DECISION
CHURN: nearly every tracked fact is corrected TWO or THREE times across the
quarter. The analyst must report the FINAL value of record and never an
intermediate one -- the harness must apply the latest correction, not echo an
earlier value.

READ-CAP SAFETY (2026-06-10): each report is kept UNDER a conservative single-read
line budget (MAX_LINES_PER_FILE) so a harness file-read tool that caps output
(commonly ~2000 lines) still sees EVERY injected fact -- including the section-8
(ACTION ITEMS) ones. A report larger than the cap would silently truncate
late-section facts and manufacture false zeros that look exactly like recall
misses (adversarial-review finding, 2026-06-10). The build ASSERTS the bound, so a
future edit that re-inflates the reports fails loudly instead of regressing. The
context pressure comes from CUMULATIVE volume across the 18 reports (well above the
~300-400K effective-attention knee, backlog/2026-06-01-methodology-evidence-base.md),
not from any single oversized file; raw single-window overflow is re-confirmed
after the multi-step threading change lands (spec 2026-06-10-core-eleven-remediation, D1).

Scoring (steps/19-recall/tests/reward.py): each of the 12 facts is anchored to its
numbered answer line; +1 if that line commits to the final value (one noted prior
value is tolerated as honest disambiguation, dumping all churned values is not);
the GCP cloud proposal is a decoy that must not be adopted as the plan of record.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

PROJECT = "PROJECT VEGA"
SUBTITLE = "DATACENTER MIGRATION - WEEKLY PLATFORM REVIEW"
LINES_PER_SECTION = 180
# Conservative single-read line budget. Keep every report -- and thus every
# injected fact, even the section-8 ones -- under this so a ~2000-line-capped file
# read never truncates a late fact into a false zero. Enforced by the assert in the
# generation loop; lower LINES_PER_SECTION if a future change trips it.
MAX_LINES_PER_FILE = 1700

SECTIONS = [
    ("1. SCHEDULE & CUTOVER", "schedule"),
    ("2. STAFFING & ORGANIZATION", "staffing"),
    ("3. INFRASTRUCTURE & CAPACITY", "infra"),
    ("4. DATA & DATABASE", "data"),
    ("5. BUDGET & FINANCE", "budget"),
    ("6. RISK & COMPLIANCE", "compliance"),
    ("7. RELIABILITY & TESTING", "testing"),
    ("8. ACTION ITEMS & NOTES", "actions"),
]

SUBSYSTEMS = [
    "the load-balancer tier", "the primary database cluster", "the object store",
    "the message bus", "the auth service", "the CDN edge", "the backup pipeline",
    "the VPN gateway", "the container registry", "the secrets vault",
    "the log aggregator", "the metrics pipeline", "the DNS zone",
    "the firewall ruleset", "the service mesh",
]
TEAMS = [
    "the platform team", "the database team", "the network team", "the SRE cell",
    "the security group", "the release desk", "the capacity group",
    "the architecture board", "the QA cell",
]
VERBS = [
    "migrated", "rebaselined", "load-tested", "profiled", "cut over",
    "validated", "audited", "benchmarked", "stress-tested", "rehearsed",
]
METRICS = [
    "p99 latency", "error budget", "replication lag", "throughput",
    "failover time", "cache hit rate", "saturation", "request rate",
]
OUTCOMES = [
    "within tolerance", "nominal against the baseline", "trending favourably",
    "flagged for a follow-up cycle", "carried into next week's agenda",
    "closed with no further action", "escalated to the architecture board",
]


def filler_line(section, wk, idx):
    sub = SUBSYSTEMS[(wk * 7 + idx) % len(SUBSYSTEMS)]
    team = TEAMS[(wk * 3 + idx) % len(TEAMS)]
    verb = VERBS[(wk + idx) % len(VERBS)]
    metric = METRICS[(wk * 5 + idx) % len(METRICS)]
    out = OUTCOMES[(wk * 2 + idx) % len(OUTCOMES)]
    forms = {
        "schedule": f"Cutover item C-{wk:02d}{idx:03d}: {team} {verb} {sub}; the {metric} was {out}.",
        "staffing": f"{team} reported {sub} staffing at planned levels; ramp item {wk:02d}{idx:03d} stays {out}.",
        "infra": f"Capacity line I-{wk:02d}{idx:03d} covering {sub} was {verb} and is {out}.",
        "data": f"Data note D-{wk:02d}{idx:03d}: {sub} was {verb} by {team}; {metric} {out}.",
        "budget": f"Cost line B-{wk:02d}{idx:03d} for {sub} was {verb}; spend variance {out}.",
        "compliance": f"Risk item R-{wk:02d}{idx:03d} on {sub} was {verb} by {team} and is {out}.",
        "testing": f"Test run T-{wk:02d}{idx:03d}: {team} {verb} {sub}; measured {metric} was {out}.",
        "actions": f"Action A-{wk:02d}{idx:03d}: {team} to follow up on {sub}; status {out}.",
    }
    return forms[section]


# Heavy churn: most facts are restated with a revised value 2-3x across the
# quarter. Each statement reads as ordinary status prose (no marker keyword, no
# special indentation) so the current value can only be found by reading, and the
# latest statement -- which the analyst must infer supersedes the earlier ones --
# is the value of record.
INJECTIONS = {
    1: [
        ("schedule", "Schedule of record puts the migration target date at 2026-08-01."),
        ("staffing", "Maria Reyes is serving as the migration lead."),
    ],
    2: [
        ("budget", "Finance has the approved migration budget at $2.0M."),
        ("infra", "Current sizing puts the target cluster at 48 nodes."),
        ("infra", "Primary region for the build is us-east-1."),
    ],
    3: [("data", "Database direction holds the target engine at PostgreSQL 14.")],
    4: [
        ("schedule", "Cutover approach of record is big-bang."),
        ("data", "Replication topology is single-primary."),
    ],
    5: [
        ("schedule", "Revised scheduling puts the migration target date at 2026-09-15."),
        ("compliance", "Rollback window is held at 4 hours."),
    ],
    6: [
        ("infra", "Updated sizing puts the target cluster at 64 nodes."),
        ("compliance", "Compliance tier is confirmed as SOC2."),
    ],
    7: [
        ("infra", "Primary region for the build has been moved to us-west-2."),
        ("compliance", "Disaster-recovery site is Dallas."),
    ],
    8: [
        ("staffing", "Kenji Tanaka has taken over as the migration lead."),
        ("testing", "Monitoring stack is standardised on Datadog."),
    ],
    9: [("data", "Database direction holds the target engine at PostgreSQL 16.")],
    10: [("schedule", "Cutover approach of record has shifted to phased.")],
    11: [("infra", "Latest sizing puts the target cluster at 32 nodes.")],
    12: [
        ("schedule", "Rescheduled, the migration target date lands on 2026-10-30."),
        ("budget", "Finance has raised the approved migration budget to $2.8M."),
    ],
    13: [("staffing", "Amara Okafor has stepped in as the migration lead.")],
    14: [
        ("infra", "Primary region for the build has been relocated to eu-central-1."),
        ("data", "Replication topology has moved to multi-primary."),
    ],
    15: [("schedule", "Cutover approach of record is now blue-green.")],
    16: [
        ("data", "Database direction settles the target engine on Aurora."),
        ("compliance", "A proposal to switch the target cloud to GCP is under discussion only and must not be treated as the plan of record."),
    ],
    17: [("compliance", "Rollback window has been reduced to 90 minutes.")],
    18: [("actions", "Closeout week: no new baseline changes; all prior decisions of record carry forward unchanged.")],
}


def build_section(title, key, wk):
    lines = [title, "-" * len(title)]
    injected = [s for (k, s) in INJECTIONS.get(wk, []) if k == key]
    spots = sorted({(wk * 31 + i * 137) % LINES_PER_SECTION for i in range(len(injected))})
    spot_set = set(spots)
    inj_iter = iter(injected)
    for i in range(LINES_PER_SECTION):
        if i in spot_set:
            try:
                lines.append(next(inj_iter))
            except StopIteration:
                pass
        lines.append(filler_line(key, wk, i))
    for s in inj_iter:
        lines.append(s)
    lines.append("")
    return lines


total_chars = 0
for wk in range(1, 19):
    body = [
        f"{PROJECT} - {SUBTITLE}",
        f"WEEK {wk:02d} OF 18",
        "=" * 60,
        "",
        "This report records the project state for the week.",
        "",
    ]
    for title, key in SECTIONS:
        body.extend(build_section(title, key, wk))
    # Mechanical read-cap guard: if any report exceeds the single-read budget, a
    # capped read tool would drop its late-section injected facts -> false zeros.
    # Fail the build rather than ship a silently-truncating report.
    n_lines = len(body)
    assert n_lines <= MAX_LINES_PER_FILE, (
        f"week_{wk:02d} is {n_lines} lines > MAX_LINES_PER_FILE={MAX_LINES_PER_FILE}; "
        "a read-tool cap would truncate late-section facts into false zeros. "
        "Lower LINES_PER_SECTION."
    )
    text = "\n".join(body) + "\n"
    total_chars += len(text)
    with open(os.path.join(OUT_DIR, f"week_{wk:02d}.txt"), "w") as fh:
        fh.write(text)

est_tokens = total_chars / 4
print(f"VEGA: 18 reports, {total_chars} chars, ~{est_tokens:.0f} est tokens "
      f"(~{est_tokens/18:.0f}/report); window target 1,048,576")
