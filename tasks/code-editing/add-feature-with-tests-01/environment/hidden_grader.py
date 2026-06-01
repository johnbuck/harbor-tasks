"""Hidden grader for the full LRUCache contract (baked at /opt/canonical/, not
visible to the agent at /app). Emits the per-case pass list as JSON.

The visible tests cover construction/get/put/eviction/recency. The gradient
cases are capacity validation (ValueError on capacity < 1), peek() that does
NOT refresh recency, __len__, and correctness under heavy churn — a minimal
OrderedDict implementation that only supports get/put passes the visible tests
but lacks peek/validation/__len__ and lands a partial reward.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from lru import LRUCache
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

results = {}


def check(name, fn):
    try:
        results[name] = bool(fn())
    except Exception:
        results[name] = False


# basic (also visible — kept for self-containment)
def _basic():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    return c.get("a") == 1 and c.get("b") == 2


check("basic_get_put", _basic)


def _eviction():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts a
    return c.get("a") == -1 and c.get("b") == 2 and c.get("c") == 3


check("eviction", _eviction)


def _get_refreshes():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)  # should evict b, not a
    return c.get("a") == 1 and c.get("b") == -1


check("get_refreshes_recency", _get_refreshes)


# capacity validation
def _capacity_zero_raises():
    try:
        LRUCache(0)
    except ValueError:
        return True
    return False


check("capacity_zero_raises", _capacity_zero_raises)


def _capacity_negative_raises():
    try:
        LRUCache(-3)
    except ValueError:
        return True
    return False


check("capacity_negative_raises", _capacity_negative_raises)


# peek() does NOT refresh recency
def _peek_returns_value():
    c = LRUCache(2)
    c.put("a", 1)
    return c.peek("a") == 1


check("peek_returns_value", _peek_returns_value)


def _peek_absent():
    c = LRUCache(2)
    return c.peek("nope") == -1


check("peek_absent_minus_one", _peek_absent)


def _peek_does_not_refresh():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.peek("a")    # must NOT refresh "a"
    c.put("c", 3)  # "a" is still LRU -> evict "a"
    return c.get("a") == -1 and c.get("b") == 2 and c.get("c") == 3


check("peek_does_not_refresh", _peek_does_not_refresh)


# __len__
def _len_tracks():
    c = LRUCache(2)
    if len(c) != 0:
        return False
    c.put("a", 1)
    if len(c) != 1:
        return False
    c.put("b", 2)
    c.put("c", 3)  # evicts a, len stays 2
    return len(c) == 2


check("len_tracks_and_caps", _len_tracks)


# heavy churn correctness vs a reference LRU
def _churn():
    from collections import OrderedDict

    ref = OrderedDict()
    cap = 4
    c = LRUCache(cap)
    keys = list(range(10))
    seq = []
    # deterministic pseudo-sequence of ops
    x = 7
    for _ in range(400):
        x = (x * 1103515245 + 12345) % 100
        seq.append(x)
    for s in seq:
        k = keys[s % len(keys)]
        if s % 3 == 0:
            # put
            c.put(k, s)
            if k in ref:
                ref.move_to_end(k)
            ref[k] = s
            if len(ref) > cap:
                ref.popitem(last=False)
        else:
            # get
            got = c.get(k)
            if k in ref:
                expected = ref[k]
                ref.move_to_end(k)
            else:
                expected = -1
            if got != expected:
                return False
    return True


check("heavy_churn_matches_reference", _churn)

print(json.dumps(results))
