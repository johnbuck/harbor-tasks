A small geometry package lives under `/app`:

- `/app/geometry/shapes.py` — shape classes (`Circle`, `Rectangle`), each with `area()`.
- `/app/geometry/__init__.py` — package exports.
- `/app/main.py` — `total_area(shapes)`, currently using `isinstance` branches.

A failing test suite at `/app/tests/test_geometry.py` requires two things:

1. Add a `Triangle(base, height)` class to `geometry/shapes.py` with an
   `area()` method (area = 0.5 · base · height), exported from the package.
2. Make `total_area(shapes)` work for **any** object exposing `.area()` —
   not just the known classes. (One test passes in a shape type that doesn't
   exist in `shapes.py`, so adding another `isinstance` branch won't pass it.)

Constraints:

- Do not modify the test file.
- Keep existing behavior (Circle, Rectangle) intact.

Run the tests with:

```
cd /app && python -m pytest tests/test_geometry.py -v
```

When all tests pass, you are done.
