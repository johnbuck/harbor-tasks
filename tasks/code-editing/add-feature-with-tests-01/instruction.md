Implement the `LRUCache` class in `/app/lru.py`. The stub raises
`NotImplementedError`; a visible test suite at `/app/tests/test_lru.py` defines
the basic behavior, but the **full contract below** is what's graded.

## Contract for `LRUCache`

- `LRUCache(capacity: int)` — fixed capacity. **`capacity` must be `>= 1`;**
  a capacity `< 1` must raise `ValueError` at construction time.
- `get(key) -> value | -1` — return the value, or `-1` if absent. A `get`
  counts as a use and **refreshes** the key's recency.
- `put(key, value)` — insert or update. A `put` counts as a use (refreshes
  recency). When inserting a **new** key would exceed capacity, evict the
  least-recently-used entry first. Updating an **existing** key refreshes its
  recency and does **not** evict.
- `peek(key) -> value | -1` — return the value (or `-1` if absent) **without**
  counting as a use: `peek` must **not** change recency. This is the key
  distinction the visible tests don't exercise.
- `__len__()` — number of entries currently cached (never exceeds capacity).

The cache must remain correct under heavy churn (many puts/gets/evictions) and
must never hold more than `capacity` entries.

The visible tests cover construction, get/put, eviction, and recency on
get/put. The **capacity validation**, **`peek` (no-refresh)**, and
**`__len__`** rules are part of the contract and are checked by a hidden grader
— implement the whole contract, not just enough to make the visible tests green.

## Constraints

- Do **not** modify the test file `/app/tests/test_lru.py`.
- Keep the public interface (`get`, `put`, `peek`, `__len__`) exactly as the
  contract describes.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

Run the visible tests with:

```
cd /app && python -m pytest tests/test_lru.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks capacity validation, `peek` (no recency
refresh), and `__len__`.
