A small geometry package lives under `/app`:

- `/app/geometry/shapes.py` — shape classes (`Circle`, `Rectangle`), each with
  an `area()` method.
- `/app/geometry/__init__.py` — package exports.
- `/app/main.py` — `total_area(shapes)`, currently using `isinstance` branches.

A visible test suite at `/app/tests/test_geometry.py` covers the basics, but
the **full contract below** is what's graded.

## Contract

1. **Add a `Triangle(base, height)` class** to `geometry/shapes.py` with an
   `area()` method (`area = 0.5 · base · height`).
2. **Export `Triangle` from the package**, so that **both**
   `from geometry.shapes import Triangle` **and** `from geometry import Triangle`
   work. (`Circle` and `Rectangle` must remain importable both ways too.)
3. **Make `total_area(shapes)` polymorphic** — it must sum `.area()` over *any*
   object exposing an `area()` method, **without** enumerating known classes.
   Adding another `isinstance` branch is **not** an acceptable solution: the
   refactor must remove the type-dispatch entirely.
4. `total_area([])` returns `0.0`.
5. If an element does **not** expose a callable `area()`, `total_area` must
   raise (let the natural `AttributeError`/`TypeError` propagate) rather than
   silently skipping it.

This is a **refactor**: keep existing `Circle`/`Rectangle` behavior intact,
make only the changes the contract requires, and leave **no dead code** behind
— in particular `main.py` should no longer contain `isinstance` dispatch or
imports it no longer uses.

The visible tests cover the `Triangle` area, a mixed-known total, and one
duck-typed unknown shape. The package-level `Triangle` export, the
empty-list result, the raise-on-non-shape rule, and the no-dead-code quality
bar are part of the contract and are checked by a hidden grader.

## Constraints

- Do **not** modify the test file `/app/tests/test_geometry.py`.
- Keep `Circle`/`Rectangle` behavior intact.
- Keep the code clean: no debug `print()`s, no leftover dead code.

Run the visible tests with:

```
cd /app && python -m pytest tests/test_geometry.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit.
