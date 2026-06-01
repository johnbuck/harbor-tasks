"""Hidden grader for the full running_total contract (baked at /opt/canonical/,
not visible to the agent at /app). Emits the per-case pass list as JSON so the
verifier can grade completeness across the contract's edge cases.

The visible tests cover only the basic off-by-one + empty cases. The no-mutation
and None-gap cases here are the gradient: a naive `range(0, len(nums))` fix
passes the basics but mutates nothing yet CRASHES on a None entry (TypeError on
`total += None`), so it fails the gap cases and lands a partial reward.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from running_total import running_total
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

results = {}


def check(name, fn):
    try:
        results[name] = bool(fn())
    except Exception:
        results[name] = False


# rule 1 (also visible — kept so the grader is self-contained)
check("basic", lambda: running_total([1, 2, 3]) == [1, 3, 6])
check("empty", lambda: running_total([]) == [])
check("single", lambda: running_total([5]) == [5])
check("negatives", lambda: running_total([3, -1, -1]) == [3, 2, 1])

# rule 3: input must not be mutated
def _no_mutation():
    src = [1, 2, 3]
    running_total(src)
    return src == [1, 2, 3]


check("no_mutation", _no_mutation)


def _no_mutation_returns_new_list():
    src = [4, 5]
    out = running_total(src)
    return out is not src


check("returns_new_list", _no_mutation_returns_new_list)

# rule 4 + 5: None is a gap (contributes 0, still one element per position)
check("none_gap_middle", lambda: running_total([1, None, 2]) == [1, 1, 3])
check("none_gap_leading", lambda: running_total([None, 3]) == [0, 3])
check("none_gap_trailing", lambda: running_total([2, None]) == [2, 2])
check("none_only", lambda: running_total([None, None]) == [0, 0])
check(
    "none_with_negatives",
    lambda: running_total([5, None, -2, None, 1]) == [5, 5, 3, 3, 4],
)

print(json.dumps(results))
