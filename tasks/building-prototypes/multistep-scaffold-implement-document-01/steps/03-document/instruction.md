# Step 3 — Write the README (must match the implementation)

Write a `/app/README.md` that documents the `calc` package **as you actually built it**.

The README must include:

- A brief description of what the package does.
- Installation / setup notes.
- An **API reference for ALL FOUR functions** — `add`, `sub`, `mul`, and
  `divide` — each with its parameters and return value.
- For `divide`, the docs must state both that it returns a **float** and that it
  **raises `ZeroDivisionError`** when the divisor is `0`.
- At least one **fenced code block** (```` ```python ````) with a runnable usage
  example that calls the functions and prints results. The example must be
  accurate: any output you show in a comment must match what the code really
  prints (e.g. `divide(10, 2)` prints `5.0`, not `5`).

This step is graded on whether the documentation **matches the implementation**:
a README that omits a function, mis-states the divide-by-zero behavior, or shows
a usage example that does not actually run will lose points.
