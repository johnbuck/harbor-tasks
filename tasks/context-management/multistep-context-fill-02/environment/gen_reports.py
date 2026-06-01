#!/usr/bin/env python3
"""Generate 18 weekly status reports for PROJECT VEGA (datacenter migration).

CONTEXT-SATURATION ladder rung 2 of 3 = UPDATE-CHURN. Same 1M-window overflow as
rung 1 (~72K tokens/report, ~1.3M cumulative), but the stressor is DECISION CHURN:
nearly every tracked fact is corrected TWO or THREE times across the quarter. The
analyst must report the FINAL value of record and never an intermediate one. This
isolates stale-value surfacing under a full window -- the harness must apply the
latest correction, not echo an earlier (and now in- or out-of-window) value.

Scoring (steps/19-recall/tests/test.sh): +1 per final value, -1 per superseded
value (each fact may have up to TWO stale values), -1 for the DRAFT GCP decoy.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

PROJECT = "PROJECT VEGA"
SUBTITLE = "DATACENTER MIGRATION - WEEKLY PLATFORM REVIEW"
LINES_PER_SECTION = 300

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


# Heavy churn: most facts corrected 2-3x. Final value = last statement.
INJECTIONS = {
    1: [
        ("schedule", "The migration target date is set to 2026-08-01."),
        ("staffing", "Migration lead: Maria Reyes."),
    ],
    2: [
        ("budget", "The approved migration budget is $2.0M."),
        ("infra", "The target cluster is sized at 48 nodes."),
        ("infra", "The primary region is us-east-1."),
    ],
    3: [("data", "The target database engine is PostgreSQL 14.")],
    4: [
        ("schedule", "The cutover strategy is big-bang."),
        ("data", "Replication topology is single-primary."),
    ],
    5: [
        ("schedule", "CORRECTION: the migration target date moves from 2026-08-01 to 2026-09-15."),
        ("compliance", "The rollback window is 4 hours."),
    ],
    6: [
        ("infra", "CORRECTION: the cluster is resized from 48 nodes to 64 nodes."),
        ("compliance", "Compliance tier is confirmed as SOC2."),
    ],
    7: [
        ("infra", "CORRECTION: the primary region moves from us-east-1 to us-west-2."),
        ("compliance", "The disaster-recovery site is Dallas."),
    ],
    8: [
        ("staffing", "CORRECTION: migration lead changes from Maria Reyes to Kenji Tanaka."),
        ("testing", "The monitoring stack is standardised on Datadog."),
    ],
    9: [("data", "CORRECTION: the target database engine moves from PostgreSQL 14 to PostgreSQL 16.")],
    10: [("schedule", "CORRECTION: the cutover strategy changes from big-bang to phased.")],
    11: [("infra", "CORRECTION (final): the cluster is resized again from 64 nodes to 32 nodes.")],
    12: [
        ("schedule", "CORRECTION (final): the migration target date moves from 2026-09-15 to 2026-10-30."),
        ("budget", "CORRECTION (final): the migration budget is raised from $2.0M to $2.8M."),
    ],
    13: [("staffing", "CORRECTION (final): migration lead changes from Kenji Tanaka to Amara Okafor.")],
    14: [
        ("infra", "CORRECTION (final): the primary region moves from us-west-2 to eu-central-1."),
        ("data", "CORRECTION (final): replication topology changes from single-primary to multi-primary."),
    ],
    15: [("schedule", "CORRECTION (final): the cutover strategy changes from phased to blue-green.")],
    16: [
        ("data", "CORRECTION (final): the target database engine moves from PostgreSQL 16 to Aurora."),
        ("compliance", "DRAFT - NOT APPROVED: a proposal to switch the target cloud to GCP is under discussion only and must not be treated as the plan of record."),
    ],
    17: [("compliance", "CORRECTION (final): the rollback window is reduced from 4 hours to 90 minutes.")],
    18: [("actions", "Closeout week: no new baseline changes; all prior decisions of record stand as last stated.")],
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
        f"{PROJECT} - {SUBTITLE}",
        f"WEEK {wk:02d} OF 18",
        "=" * 60,
        "",
        "This report records the project state for the week. Decisions are revised",
        "frequently; the value that counts for any item is always the LATEST one",
        "stated, even when it was changed earlier in the program.",
        "",
    ]
    for title, key in SECTIONS:
        body.extend(build_section(title, key, wk))
    text = "\n".join(body) + "\n"
    total_chars += len(text)
    with open(os.path.join(OUT_DIR, f"week_{wk:02d}.txt"), "w") as fh:
        fh.write(text)

est_tokens = total_chars / 4
print(f"VEGA: 18 reports, {total_chars} chars, ~{est_tokens:.0f} est tokens "
      f"(~{est_tokens/18:.0f}/report); window target 1,048,576")
