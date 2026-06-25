#!/bin/bash
# Reference solution — implements the FULL contract (get/put with LRU eviction
# and recency, capacity validation, peek without refresh, __len__). Scores 1.0.
set -e

cat > /app/lru.py <<'EOF'
"""LRU cache implementing the LRUCache contract."""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._data: "OrderedDict" = OrderedDict()

    def get(self, key):
        if key not in self._data:
            return -1
        self._data.move_to_end(key)
        return self._data[key]

    def peek(self, key):
        # Read WITHOUT counting as a use — recency is not changed.
        return self._data.get(key, -1)

    def put(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self):
        return len(self._data)
EOF
