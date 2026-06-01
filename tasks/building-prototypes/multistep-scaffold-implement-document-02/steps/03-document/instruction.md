# Step 3 — Write the README (must match the implementation)

Write a `/app/README.md` that documents the `textkit` package **as you actually built it**.

The README must include:

- A brief description of what the package does.
- Installation / setup notes.
- An **API reference for ALL THREE functions** — `slugify`, `truncate`, and
  `word_count` — each with its parameter(s) and return value.
- For `truncate`, the docs must state the **suffix-aware length contract**: the
  returned string is at most `n` characters *including* the suffix (so
  `truncate("hello world", 8)` is `"hello..."`, not `"hello wo..."`), and that
  the `suffix` argument defaults to `"..."`.
- At least one **fenced code block** (```` ```python ````) with a runnable usage
  example that calls the functions and prints results. Any output shown in a
  trailing `# comment` must match what the code really prints (e.g.
  `truncate("hello world", 8)` prints `hello...`).

This step is graded on whether the documentation **matches the implementation**:
omitting a function, mis-stating the truncate length rule, or an example that
does not actually run will lose points.
