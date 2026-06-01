# Step 3 — Write the README (must match the implementation)

Write a `/app/README.md` that documents the `tempconv` package **as you actually built it**.

The README must include:

- A brief description of what the package does.
- Installation / setup notes.
- An **API reference for ALL THREE functions** — `c_to_f`, `f_to_c`, and
  `round_temp` — each with its parameter(s), formula (where applicable), and
  return value.
- The docs must state that `c_to_f` and `f_to_c` **raise `ValueError` for
  temperatures below absolute zero** (below `-273.15` °C / `-459.67` °F).
- At least one **fenced code block** (```` ```python ````) with a runnable usage
  example that calls the functions and prints results. Any output shown in a
  trailing `# comment` must match what the code really prints (e.g. `c_to_f(100)`
  prints `212.0`, `f_to_c(32)` prints `0.0`).

This step is graded on whether the documentation **matches the implementation**:
omitting a function, failing to document the absolute-zero `ValueError`, or an
example that does not actually run will lose points.
