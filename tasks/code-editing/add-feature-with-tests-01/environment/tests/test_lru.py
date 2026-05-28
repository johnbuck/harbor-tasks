from lru import LRUCache


def test_get_absent_returns_minus_one():
    c = LRUCache(2)
    assert c.get("missing") == -1


def test_put_then_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_update_existing_key():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("a", 99)
    assert c.get("a") == 99


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a" (LRU)
    assert c.get("a") == -1
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1  # "a" now most-recently-used
    c.put("c", 3)           # evicts "b", not "a"
    assert c.get("a") == 1
    assert c.get("b") == -1
    assert c.get("c") == 3


def test_update_refreshes_recency_no_evict():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # update refreshes "a"; capacity still 2
    c.put("c", 3)   # evicts "b" (LRU), not "a"
    assert c.get("a") == 10
    assert c.get("b") == -1
    assert c.get("c") == 3


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)  # evicts "a"
    assert c.get("a") == -1
    assert c.get("b") == 2
