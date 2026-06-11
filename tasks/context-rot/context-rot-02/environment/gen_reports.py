#!/usr/bin/env python3
"""Generate 18 inspection reports for THE WESTMARCH PRIORY CONSERVATION SURVEY.

CONTEXT-ROT, MULTI-HOP variant (rung 2 of the rot family). The 18 records
(~345K tokens << the 1M deepseek-v4-pro window, deep in the ~300-400K rot zone,
NO overflow) are read one-per-step across 18 ingest steps that THREAD into ONE
growing conversation (the task image bakes /opt/harness/thread-session; the thin
adapters resume the session each step), so the records ACCUMULATE in-context and
the buried facts are genuinely subject to lost-in-the-middle rot. Without that
marker each ingest would run fresh and nothing would accumulate (the pre-2026-06-10
bug that made this a memory test). Recall requires CHAINING TWO facts buried at
different conversational depths:

    anchor fact  : "<feature> was made by/of <BRIDGE entity>"   (depth A)
    bridge fact  : "<BRIDGE entity> has <attribute>"            (depth B)
    question     : "what is <attribute> of the <BRIDGE for feature>?"  -> attribute

Both hops must survive for the chain to resolve, so rot on EITHER hop breaks it
(RULER variable-tracking). 8 chains = 16 needles, bucketed by depth:
  * EARLY chains (both hops in visits 2-6)  -> primacy-protected, should survive
  * MIDDLE chains (both hops in visits 8-12) -> lost-in-the-middle, rot-critical
  * LATE chains (both hops in visits 14-18) -> recency-protected, should survive
Reward is matched/8 (steps/19-recall/tests/reward.py). The early/middle/late
fractions are DIAGNOSTIC ONLY (weight-0): since the harness may also externalize
to its hindsight MCP, the depth split is an observation of WHERE answers failed,
not a load-bearing "rot curve" claim. Questions PARAPHRASE the bridge link
(NoLiMa); no instruction mentions burial, hops, or rot. Reports wiped before recall.
"""
import os

OUT_DIR = "/app/reports"
os.makedirs(OUT_DIR, exist_ok=True)

PROJECT = "THE WESTMARCH PRIORY CONSERVATION SURVEY"
SUBTITLE = "ROOM-BY-ROOM FABRIC INSPECTION - WEEKLY VISIT RECORD"

# ~80 lines/section x 8 sections x 18 visits ~= 345K tokens (in-window rot zone).
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
    "the cloister arcade", "the lancet windows", "the parapet coping",
    "the lime render", "the ashlar facing", "the lead flashings",
    "the oak screen", "the stone reredos", "the wrought-iron grille",
    "the traceried mullions", "the precinct wall", "the gate arch",
    "the choir stalls", "the rood loft", "the floor ledgers",
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


# 8 two-hop chains = 16 needles. (section, sentence) per visit. Two visits (9, 18)
# carry two needles, placed in DIFFERENT sections.
INJECTIONS = {
    # --- EARLY chains (both hops visits 2-6) ---
    2:  [("rooms", "The cloister vaulting was designed by the architect Crispin Vael.")],            # C-E1 anchor
    4:  [("recs", "Crispin Vael trained as an architect in the city of Lyon.")],                     # C-E1 bridge -> Lyon
    3:  [("joinery", "The refectory floor tiles were fired by the Maw and Co pottery.")],            # C-E2 anchor
    6:  [("grounds", "The Maw and Co pottery was based in the town of Jackfield.")],                 # C-E2 bridge -> Jackfield
    # --- MIDDLE chains (both hops visits 8-12) -- ROT-CRITICAL ---
    8:  [("services", "The scriptorium windows are glazed with glass from the Whitefriars works.")], # C-M1 anchor
    10: [("grounds", "The Whitefriars works stood on the bank of the river Thames.")],               # C-M1 bridge -> Thames
    9:  [
        ("joinery", "The prior's lodging staircase was built by the joiner Hugh Tarrant."),          # C-M2 anchor
        ("rooms", "The chapter house floor is paved in Frosterley marble."),                         # C-M3 anchor
    ],
    11: [("recs", "Hugh Tarrant rose to become master of the Guild of Saint Luke.")],                # C-M2 bridge -> Saint Luke
    12: [("defects", "Frosterley marble is a dark limestone quarried in County Durham.")],           # C-M3 bridge -> Durham
    # --- LATE chains (both hops visits 14-18) ---
    15: [("exterior", "The gatehouse lantern was wrought by the smith Owen Brace.")],                # C-L1 anchor
    17: [("recs", "Owen Brace kept his forge in the city of Hereford.")],                            # C-L1 bridge -> Hereford
    16: [("services", "The bell tower carillon was founded by the Taylor foundry.")],                # C-L2 anchor
    14: [("roof", "The dorter roof timbers are of Baltic oak shipped through the port of Riga.")],   # C-L3 anchor
    18: [
        ("services", "The Taylor foundry has its bell-works in the town of Loughborough."),          # C-L2 bridge -> Loughborough
        ("grounds", "The port of Riga lies on the coast of the Baltic country of Latvia."),          # C-L3 bridge -> Latvia
    ],
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
