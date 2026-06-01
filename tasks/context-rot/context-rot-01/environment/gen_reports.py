#!/usr/bin/env python3
"""Generate 18 inspection reports for THE MERIDIAN HALL CONSERVATION SURVEY.

This is a CONTEXT-ROT test, NOT a context-overflow test (that is the
multistep-context-fill / "management" family). The two differ by REGIME:

  * OVERFLOW (management): corpus EXCEEDS the model window -> the harness is
    FORCED to compact/evict. Tests survival under forced pressure.
  * ROT (this task): corpus FITS inside the window (~350K tokens << the
    1,048,576 deepseek-v4-pro window) but sits in the empirical degradation zone
    (~300-400K, per Chroma "Context Rot" for 1M-class models). Nothing is forced
    out. It tests whether the harness PROACTIVELY manages context (re-surfaces /
    externalises / indexes) to beat positional rot it is NOT forced to handle. A
    naive harness that just lets 350K sit raw in the window suffers
    lost-in-the-middle rot; a harness with active context hygiene flattens it.

Design (grounded in the long-context literature):
  * Lost-in-the-Middle (Liu et al. 2023): facts buried in the MIDDLE of a long
    context degrade most. 12 needles are planted at controlled conversational
    DEPTH -- 4 EARLY (reports 2-6), 4 MIDDLE (reports 8-12), 4 LATE (reports
    14-18) -- so the scorer reads the rot CURVE (middle << edges = rot; flat =
    the harness mitigated).
  * NoLiMa (Modarressi et al. 2025): a needle that lexically matches the question
    only tests retrieval (grep). Each needle here is phrased so the recall
    question PARAPHRASES it (orangery->conservatory, balustrade->railing, clock
    tower->bell tower), forcing association -- which is what rots.
  * No memory crutch: reports are DELETED before recall (workdir/setup.sh), so
    the answer comes from in-context memory, not a re-read. No instruction tells
    the agent facts are buried or to take notes -- the SCENARIO carries it.

Canonical answers + per-position scoring live in steps/19-recall/tests/test.sh.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

PROJECT = "THE MERIDIAN HALL CONSERVATION SURVEY"
SUBTITLE = "ROOM-BY-ROOM FABRIC INSPECTION - WEEKLY VISIT RECORD"

# Each report targets ~19K tokens (~76K chars) so 18 reports ~= 345K tokens:
# deep in the ~300-400K rot zone, but well inside the 1M window (NO overflow).
# ~80 lines/section x 8 sections.
LINES_PER_SECTION = 80

SECTIONS = [
    ("1. EXTERIOR FABRIC", "exterior"),
    ("2. ROOF & RAINWATER GOODS", "roof"),
    ("3. PRINCIPAL ROOMS", "rooms"),
    ("4. JOINERY & PLASTERWORK", "joinery"),
    ("5. SERVICES & ENVIRONMENT", "services"),
    ("6. GROUNDS & OUTBUILDINGS", "grounds"),
    ("7. CONDITION & DEFECTS", "defects"),
    ("8. RECOMMENDATIONS", "recs"),
]

ELEMENTS = [
    "the cornice mouldings", "the sash windows", "the parapet coping",
    "the lime render", "the ashlar facing", "the lead flashings",
    "the oak panelling", "the marble chimneypiece", "the wrought-iron railings",
    "the stone mullions", "the boundary wall", "the carriage arch",
    "the dado rail", "the picture rail", "the skirting boards",
]
TRADES = [
    "the masonry team", "the joinery workshop", "the roofing contractor",
    "the plastering crew", "the metalwork specialist", "the glazing subcontractor",
    "the conservation surveyor", "the structural engineer", "the damp consultant",
]
ACTS = [
    "inspected", "probed", "photographed", "measured", "re-pointed where needed",
    "cleaned down", "recorded", "monitored", "assessed", "condition-graded",
]
ASPECTS = [
    "moisture ingress", "mortar loss", "timber decay", "paint adhesion",
    "stone delamination", "joint movement", "salt crystallisation", "surface soiling",
]
GRADES = [
    "graded sound with routine maintenance only", "noted as fair, monitor next visit",
    "flagged for minor repair within the year", "found stable since the last survey",
    "carried forward to the defects register", "cleared with no action required",
    "referred to the structural engineer for review",
]


def filler_line(section, wk, idx):
    """One plausible survey-record sentence, deterministic per (section,wk,idx)."""
    el = ELEMENTS[(wk * 7 + idx) % len(ELEMENTS)]
    tr = TRADES[(wk * 3 + idx) % len(TRADES)]
    act = ACTS[(wk + idx) % len(ACTS)]
    asp = ASPECTS[(wk * 5 + idx) % len(ASPECTS)]
    gr = GRADES[(wk * 2 + idx) % len(GRADES)]
    forms = {
        "exterior": f"Bay X-{wk:02d}{idx:03d}: {tr} {act} {el}; {asp} was {gr}.",
        "roof": f"Slope R-{wk:02d}{idx:03d}: {tr} {act} {el}; {asp} {gr}.",
        "rooms": f"Room note RM-{wk:02d}{idx:03d}: {el} was {act} by {tr} and {gr}.",
        "joinery": f"Joinery item J-{wk:02d}{idx:03d}: {tr} {act} {el}; {asp} {gr}.",
        "services": f"Services log SV-{wk:02d}{idx:03d}: {el} was {act}; {asp} {gr}.",
        "grounds": f"Grounds item G-{wk:02d}{idx:03d}: {tr} {act} {el}; {asp} {gr}.",
        "defects": f"Defect D-{wk:02d}{idx:03d} on {el}: {asp} was {gr}.",
        "recs": f"Recommendation C-{wk:02d}{idx:03d}: {tr} to revisit {el}; {asp} {gr}.",
    }
    return forms[section]


# report-index -> list of (section_key, needle sentence). 12 load-bearing facts.
# Each is stated ONCE, lexically LOW-OVERLAP with its recall question (the recall
# step paraphrases it). Placement controls rot position:
#   EARLY  = reports 2,3,5,6   (primacy edge)
#   MIDDLE = reports 8,9,11,12 (lost-in-the-middle -- rot-critical)
#   LATE   = reports 14,15,17,18 (recency edge)
INJECTIONS = {
    # --- EARLY ---
    2:  [("rooms", "In the Long Gallery, the timber floor is laid in reclaimed pitch pine throughout its full length.")],
    3:  [("exterior", "The orangery's glazing was supplied by the Lambeth firm Harcourt Glassworks under the original commission.")],
    5:  [("services", "Ventilation to the undercroft draws through a brick flue that the datestone records as built in 1788.")],
    6:  [("joinery", "The grand staircase balustrade is cast from a nickel-bronze alloy, unusual for a house of this date.")],
    # --- MIDDLE (rot-critical) ---
    8:  [("rooms", "The chapel's east window depicts, in stained glass, the martyrdom of Saint Aldhelm.")],
    9:  [("services", "Heating to the state rooms is delivered by a Crittall radiator system installed in the 1932 modernisation.")],
    11: [("joinery", "The library's shelving is built throughout from quarter-sawn American white oak.")],
    12: [("grounds", "The courtyard fountain is fed from an underground cistern of fourteen thousand litres capacity.")],
    # --- LATE ---
    14: [("joinery", "The billiard room ceiling carries a coffered design attributed to the architect Edwin Pugin.")],
    15: [("grounds", "The walled garden's perimeter is laid in a Flemish-bond brickwork pattern.")],
    17: [("roof", "The servants' wing roof is finished throughout with Welsh Penrhyn slate.")],
    18: [("services", "The clock tower mechanism was manufactured by Gillett and Johnston of Croydon.")],
}


def build_report(wk: int) -> str:
    lines = [
        f"{PROJECT}",
        f"{SUBTITLE}",
        f"INSPECTION VISIT {wk:02d} OF 18",
        "=" * 72,
        "",
        f"This record documents the findings of conservation inspection visit {wk:02d}.",
        "Each section reports the fabric examined this week and its condition.",
        "",
    ]
    by_sec: dict[str, list[str]] = {}
    for sec_key, sentence in INJECTIONS.get(wk, []):
        by_sec.setdefault(sec_key, []).append(sentence)
    for title, key in SECTIONS:
        lines.append(title)
        lines.append("-" * len(title))
        # plant any needle for this section near the middle of the section body
        body = [filler_line(key, wk, i) for i in range(LINES_PER_SECTION)]
        for needle in by_sec.get(key, []):
            body.insert(LINES_PER_SECTION // 2, needle)
        lines.extend(body)
        lines.append("")
    lines.append("END OF VISIT RECORD %02d" % wk)
    return "\n".join(lines)


for wk in range(1, 19):
    with open(os.path.join(OUT_DIR, f"week_{wk:02d}.txt"), "w") as f:
        f.write(build_report(wk))

print("generated 18 reports in", OUT_DIR)
