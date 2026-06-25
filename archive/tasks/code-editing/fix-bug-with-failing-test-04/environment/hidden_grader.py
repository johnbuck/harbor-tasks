"""Hidden grader for the full merge_intervals contract (baked at /opt/canonical/,
not visible to the agent at /app). Emits the per-case pass list as JSON.

The visible tests cover overlap/touching/unsorted/empty. The gradient cases are
containment, no-mutation, and the ValueError validation rule: a fix that only
flips the buggy `<` to `<=` passes the visible tests but does NOT raise on an
invalid interval and may not be mutation-safe — partial reward.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from intervals import merge_intervals
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

results = {}


def check(name, fn):
    try:
        results[name] = bool(fn())
    except Exception:
        results[name] = False


# rules 1,2,4,7 (also visible — kept for self-containment)
check("empty", lambda: merge_intervals([]) == [])
check("overlap", lambda: merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]])
check("touching", lambda: merge_intervals([[1, 2], [2, 3]]) == [[1, 3]])
check("unsorted", lambda: merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]])

# rule 3: containment
check("containment", lambda: merge_intervals([[1, 10], [2, 3]]) == [[1, 10]])
check("containment_unsorted", lambda: merge_intervals([[2, 3], [1, 10]]) == [[1, 10]])
check(
    "chained_extend",
    lambda: merge_intervals([[1, 4], [3, 6], [5, 8]]) == [[1, 8]],
)
check("zero_width_valid", lambda: merge_intervals([[5, 5], [5, 7]]) == [[5, 7]])
check(
    "zero_width_isolated",
    lambda: merge_intervals([[1, 1], [3, 3]]) == [[1, 1], [3, 3]],
)

# rule 5: no mutation of input
def _no_mutation():
    src = [[3, 6], [1, 4]]
    snapshot = [list(x) for x in src]
    merge_intervals(src)
    return src == snapshot


check("no_mutation", _no_mutation)


def _new_inner_lists():
    a = [1, 4]
    out = merge_intervals([a, [10, 12]])
    # the returned [1,4] must not be the SAME object as the caller's list
    return all(o is not a for o in out)


check("returns_new_inner_lists", _new_inner_lists)


# rule 6: invalid interval (start > end) raises ValueError
def _raises_on_invalid():
    try:
        merge_intervals([[5, 1]])
    except ValueError:
        return True
    return False


check("raises_valueerror_on_invalid", _raises_on_invalid)


def _raises_on_invalid_among_valid():
    try:
        merge_intervals([[1, 3], [9, 2], [4, 5]])
    except ValueError:
        return True
    return False


check("raises_valueerror_mixed", _raises_on_invalid_among_valid)


def _raises_before_merge():
    # invalid interval that would otherwise overlap a valid one
    try:
        merge_intervals([[1, 5], [4, 2]])
    except ValueError:
        return True
    return False


check("raises_valueerror_overlapping_invalid", _raises_before_merge)


def _no_mutation_with_containment():
    src = [[1, 10], [2, 3]]
    snapshot = [list(x) for x in src]
    merge_intervals(src)
    return src == snapshot


check("no_mutation_containment", _no_mutation_with_containment)

print(json.dumps(results))
