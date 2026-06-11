#!/usr/bin/env python3
"""Generator for sub-agent-parallel-decompose-01 (REDESIGN 2026-06-10).

Produces 60 HETEROGENEOUS prose word-problems that defeat the old fixed-template
KILL bug. The previous version followed one rigid sentence template with the
parity branch *pre-resolved* in the text ("because the running total is an odd
number, the supervisor adds 3"), so a ~20-line regex reproduced 60/60 answers and
a single python3 one-shotted the whole batch.

What changed to kill that:
  * variable operation COUNT (5-8 core ops) and random ORDER,
  * two DISTINCT value-dependent branch types (parity AND threshold) whose
    OUTCOME is never asserted — the rule is stated, the agent must compute the
    running total to know which arm fires,
  * DISTRACTOR sentences carrying numbers that do not touch the running count,
  * numbers rendered as a MIX of digits and spelled-out words,
  * many phrasings per operation.

A generic regex cannot reproduce the answers: it cannot resolve a value-dependent
branch without computing the running total, and it cannot tell an operative
number from a distractor without understanding the sentence.

This script is VERIFIER/ORACLE-side only. It is never copied into the agent
container (the Dockerfile copies only problems/). Run it to regenerate the three
artifacts in lock-step:

    python3 solution/gen.py            # writes problems/, tests/answers.json, prints solve.sh body

Deterministic: a fixed seed makes problems and answers reproducible together.
"""
import json
import random
from pathlib import Path

SEED = 20260610
N = 60

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
PROBLEMS = TASK / "environment" / "problems"
ANSWERS = TASK / "tests" / "answers.json"

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety"]


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + ("-" + ONES[o] if o else "")
    h, rest = divmod(n, 100)
    return ONES[h] + " hundred" + (" " + words(rest) if rest else "")


def num(rng, n: int) -> str:
    """Render n as digits or spelled-out words at random (mixed format)."""
    return words(n) if rng.random() < 0.5 else str(n)


SCENES = [
    ("harbor warehouse", "crates", "the day"),
    ("city library", "returned books", "the morning"),
    ("riverside orchard", "apple bushels", "the day"),
    ("mountain observatory", "logged comets", "the night"),
    ("community greenhouse", "seedling trays", "the day"),
    ("regional depot", "parcels", "the shift"),
    ("aquarium lab", "tagged fish", "the day"),
    ("bakery cooperative", "sourdough loaves", "the morning"),
    ("bicycle workshop", "repaired frames", "the day"),
    ("recycling center", "sorted bins", "the shift"),
    ("seed bank", "labelled samples", "the day"),
    ("printing house", "bound volumes", "the day"),
]

ADD = [
    "a delivery brings {x} more {u}",
    "the crew restocks {x} additional {u}",
    "{x} {u} arrive from a partner site",
    "a late shipment adds {x} {u}",
]
SUB = [
    "{x} {u} are shipped out and removed from the count",
    "{x} {u} are pulled for inspection and set aside",
    "{x} {u} are written off after a spill",
    "an order ships, taking {x} {u} away",
]
MUL = {2: ["the count is doubled when a sister site merges its stock",
           "a merger doubles the count"],
       3: ["the count is tripled after two more sites consolidate",
           "the running total is tripled by an overnight consolidation"]}

DISTRACT = [
    "The {p} is staffed by {d} people that {per}.",
    "For reference, the {p} keeps {d} aisles, though that does not change any count.",
    "A nearby sign notes the {p} was founded {d} years earlier.",
    "Background: {d} visitors toured the {p}, unrelated to the inventory.",
    "The building has {d} loading bays, a detail with no bearing on the tally.",
]


def render_parity(rng, u):
    a = rng.randint(1, 12)
    if rng.random() < 0.5:
        rule = ("if the running total is ODD at that point, {a} more {u} are added; "
                "if it is EVEN, exactly half of them are removed").format(a=num(rng, a), u=u)
        op = ("parity_odd_add_even_half", a)
    else:
        b = rng.randint(1, 9)
        rule = ("if the running total is ODD at that point, {a} {u} are removed; "
                "if it is EVEN, {b} more {u} are added").format(a=num(rng, a), b=num(rng, b), u=u)
        op = ("parity_odd_sub_even_add", a, b)
    return "a parity rule applies — " + rule, op


def render_threshold(rng, u, t_hint):
    # Pick a threshold near the plausible running total so the branch is genuinely
    # value-dependent (sometimes over, sometimes under across the 60).
    thr = max(10, t_hint + rng.randint(-25, 25))
    a = rng.randint(2, 14)
    b = rng.randint(2, 14)
    rule = ("if the running total is GREATER THAN {thr}, {a} {u} are removed; "
            "OTHERWISE {b} more {u} are added").format(thr=num(rng, thr), a=num(rng, a), b=num(rng, b), u=u)
    return "a capacity check applies — " + rule, ("threshold", thr, a, b)


def apply_op(t, op):
    kind = op[0]
    if kind == "add":
        return t + op[1]
    if kind == "sub":
        return t - op[1]
    if kind == "mul":
        return t * op[1]
    if kind == "parity_odd_add_even_half":
        return t + op[1] if t % 2 == 1 else t // 2
    if kind == "parity_odd_sub_even_add":
        return t - op[1] if t % 2 == 1 else t + op[2]
    if kind == "threshold":
        _, thr, a, b = op
        return t - a if t > thr else t + b
    raise ValueError(kind)


def build_one(rng, code):
    """Return (prose, answer, offset) or None if the roll produced a degenerate chain.

    The final answer = running_total + a per-problem calibration OFFSET that is
    NOT stated anywhere in the prose: the prose names a lookup CODE, and the
    offset for that code is served only by the latency-gated site registry (see
    main(); the agent must fetch it). This is the parser-bypass killer — a
    pure-text parser can reconstruct the running total but cannot produce the
    fact-dependent final answer, so it collapses to chance.
    """
    place, unit, period = rng.choice(SCENES)
    start = rng.randint(20, 60)
    sentences = [
        "A {p} begins {per} with {s} {u}.".format(
            p=place, per=period, s=num(rng, start), u=unit)
    ]

    n_core = rng.randint(5, 8)
    # Build a randomized op sequence. Guarantee >=1 value-dependent branch,
    # allow up to 2; the rest are add/sub/mul.
    n_branch = rng.choice([1, 1, 2])
    n_mul = rng.choice([0, 1, 1])
    n_plain = n_core - n_branch - n_mul
    if n_plain < 2:
        return None

    slots = (["branch"] * n_branch) + (["mul"] * n_mul) + (["plain"] * n_plain)
    # mul must not be the first core op (needs a value to scale); shuffle then fix.
    rng.shuffle(slots)

    rendered = []  # (text, op)
    for slot in slots:
        if slot == "plain":
            if rng.random() < 0.5:
                x = rng.randint(3, 15)
                rendered.append((rng.choice(ADD).format(x=num(rng, x), u=unit), ("add", x)))
            else:
                x = rng.randint(3, 18)
                rendered.append((rng.choice(SUB).format(x=num(rng, x), u=unit), ("sub", x)))
        elif slot == "mul":
            m = rng.choice([2, 3])
            rendered.append((rng.choice(MUL[m]), ("mul", m)))
        else:  # branch
            if rng.random() < 0.5:
                rendered.append(render_parity(rng, unit))
            else:
                rendered.append(render_threshold(rng, unit, t_hint=start))

    # Ensure a mul is never first (so it actually scales accumulated work).
    for i, (_, op) in enumerate(rendered):
        if op[0] == "mul" and i == 0:
            rendered[0], rendered[1] = rendered[1], rendered[0]
            break

    # Simulate, abort on any negative intermediate.
    sim = start
    for _, op in rendered:
        sim = apply_op(sim, op)
        if sim < 1:
            return None
    base = sim
    # Leave headroom for the calibration offset so the final answer stays in range.
    if not (5 <= base <= 450) or base == start:
        return None
    offset = rng.randint(11, 49)   # per-problem; served only by the gated registry
    answer = base + offset

    # Stitch prose with light connective variety, inserting 1-3 distractors.
    connectors = ["Then, ", "Next, ", "After that, ", "Later, ", "Soon after, ",
                  "By midday, ", "In the afternoon, ", "Before closing, "]
    body = list(rendered)
    n_distract = rng.randint(1, 3)
    insert_points = sorted(rng.sample(range(len(body) + 1), n_distract))
    out_sentences = []
    bi = 0
    distract_done = 0
    for pos in range(len(body) + 1):
        while distract_done < n_distract and insert_points[distract_done] == pos:
            d = rng.randint(2, 90)
            out_sentences.append(rng.choice(DISTRACT).format(
                p=place, d=num(rng, d), per=period.replace("the ", "")))
            distract_done += 1
        if bi < len(body):
            text, _ = body[bi]
            text = text.rstrip(".")
            conn = connectors[bi % len(connectors)] if bi else "First, "
            out_sentences.append(conn + text[0].lower() + text[1:] + ".")
            bi += 1

    sentences.extend(out_sentences)
    # The final calibration step: the offset value is NOT in the prose — only the
    # lookup code is. The agent must fetch it from the gated site registry.
    sentences.append(
        "Finally, look up the calibration offset published for reference code "
        "{code} in the site registry and add that offset to the running "
        "total.".format(code=code))
    sentences.append(
        "How many {u} remain at the very end? Respond with the single final "
        "integer only.".format(u=unit))
    prose = " ".join(sentences)
    return prose, answer, offset


def main():
    rng = random.Random(SEED)
    PROBLEMS.mkdir(parents=True, exist_ok=True)
    for old in PROBLEMS.glob("*.txt"):
        old.unlink()

    answers = {}
    registry = {}   # lookup code -> calibration offset (served by the gated registry)
    i = 1
    guard = 0
    while i <= N:
        guard += 1
        if guard > 100000:
            raise RuntimeError("generator could not fill N")
        code = f"CAL-{i:02d}"
        res = build_one(rng, code)
        if res is None:
            continue
        prose, ans, offset = res
        nn = f"{i:02d}"
        (PROBLEMS / f"{nn}.txt").write_text(prose + "\n")
        answers[nn] = ans
        registry[code] = offset
        i += 1

    ANSWERS.parent.mkdir(parents=True, exist_ok=True)
    ANSWERS.write_text(json.dumps(answers, indent=2) + "\n")

    # The registry of per-problem calibration offsets is ANSWER-KEY-equivalent
    # (it determines each answer), so it lives VERIFIER-SIDE beside answers.json —
    # NOT in the agent build context (environment/) — and is derived from ANSWERS
    # so a redirected test run never mutates the repo. The latency-gated runtime
    # lookup the agent calls is installed from here by the (rebuild-deferred) gate;
    # the agent never reads this file directly. Folding the offset into each answer
    # is what makes the prose-only parser bypass collapse to chance.
    registry_path = ANSWERS.parent / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n")

    # Emit solve.sh body for the oracle.
    print("# --- solve.sh body (oracle) ---")
    for nn in sorted(answers):
        print(f"echo {answers[nn]} > /app/out/{nn}.txt")


if __name__ == "__main__":
    main()
