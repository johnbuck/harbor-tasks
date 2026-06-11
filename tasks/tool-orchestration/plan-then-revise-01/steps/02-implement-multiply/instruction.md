Step 2 of your plan. Add the remaining two planned operations to `/app/calc.py`
and register them, keeping `add`, `divide`, and the dispatch layer working.

- `multiply(a, b)` — returns `a * b`. Remember the project-wide clamp policy
  applies here too, exactly as it does to `add` and `divide`.
- `compose(first, second, a, b, c)` — chains two registered ops via the
  dispatch layer: it applies the op named `first` to `(a, b)`, then applies the
  op named `second` to `(that result, c)`. For example, with `first="add"` and
  `second="multiply"`, `compose("add", "multiply", 2, 3, 4)` is
  `multiply(add(2, 3), 4) == 20`.

Register both `multiply` and `compose` in `REGISTRY`.

The verifier will check `add`, `multiply` (incl. clamp, `multiply(50, 50) ==
1000`), `divide`, `compose`, and that `dispatch` resolves all four ops.
