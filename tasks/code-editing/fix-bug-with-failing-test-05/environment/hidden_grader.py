"""Hidden grader for the full flatten contract (baked at /opt/canonical/, not
visible to the agent at /app). Emits the per-case pass list as JSON.

The visible tests cover lists + strings-as-atoms. The gradient cases are tuple
flattening, non-list/tuple iterables preserved as atoms (dict, set), and
no-mutation: a fix that recurses only on `list` passes the visible tests but
FAILS the tuple cases — partial reward.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from flatten import flatten
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

results = {}


def check(name, fn):
    try:
        results[name] = bool(fn())
    except Exception:
        results[name] = False


# rules 1,3,6 (also visible — kept for self-containment)
check("empty", lambda: flatten([]) == [])
check("already_flat", lambda: flatten([1, 2, 3]) == [1, 2, 3])
check("deep_lists", lambda: flatten([1, [2, [3, [4, 5]]], 6]) == [1, 2, 3, 4, 5, 6])
check("strings_are_atoms", lambda: flatten(["ab", ["cd"]]) == ["ab", "cd"])

# rule 2: tuples flatten (every case here is missed by a list-only recursion)
check("tuple_basic", lambda: flatten([1, (2, 3), 4]) == [1, 2, 3, 4])
check("tuple_nested", lambda: flatten([1, (2, [3, (4, 5)]), 6]) == [1, 2, 3, 4, 5, 6])
check("mixed_list_tuple", lambda: flatten([[1, (2,)], (3, [4])]) == [1, 2, 3, 4])
check("tuple_of_tuples", lambda: flatten([((1, 2), (3, 4))]) == [1, 2, 3, 4])
check("singleton_tuple", lambda: flatten([(1,), (2,)]) == [1, 2])

# rule 3 extended: single-char and empty string atoms
check("char_string_atom", lambda: flatten(["a", "b", "c"]) == ["a", "b", "c"])
check("empty_string_atom", lambda: flatten(["", ["x"]]) == ["", "x"])
check("bytes_atom", lambda: flatten([b"ab", [b"cd"]]) == [b"ab", b"cd"])

# rule 4: non-list/tuple iterables are atoms
check("dict_atom", lambda: flatten([1, {"k": 1}, [2]]) == [1, {"k": 1}, 2])
check("set_atom", lambda: flatten([1, {2, 3}, 4]) == [1, {2, 3}, 4])
check("none_kept", lambda: flatten([None, [None]]) == [None, None])

# rule 5: no mutation of input
def _no_mutation():
    src = [1, [2, 3]]
    flatten(src)
    return src == [1, [2, 3]]


check("no_mutation", _no_mutation)

print(json.dumps(results))
