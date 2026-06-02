Step 2 of your plan. Add `multiply(a: int, b: int) -> int` to `/app/calc.py`
that returns `a * b`. Keep `add` working. Remember the project-wide clamp policy
applies here too — `multiply` must clamp its result like `add` does.

The verifier will check `add(2, 3) == 5`, `multiply(4, 5) == 20`, and that the
clamp still holds (`multiply(50, 50) == 1000`).
