You are building a small Python module `/app/calc.py` over the next 4 steps.

**Before writing any code**, write a short plan to `/app/PLAN.md` describing
the 4 functions you'll implement (function names, expected signatures,
expected behavior). Treat this as a one-time plan you'll execute step by step.

**Project-wide rule (decided at kickoff — applies to EVERY arithmetic function
in this module, now and later):** every result must be **clamped to the
inclusive range [-1000, 1000]**. If a computed value exceeds 1000 it becomes
1000; if it is below -1000 it becomes -1000. Implement this as a shared helper
(e.g. `_clamp`) so all functions apply the identical policy. Record this rule in
your PLAN.md so you don't lose it.

Then **for this step (step 1)**, implement just the first function:

```python
def add(a: int, b: int) -> int:
    """Return a + b, clamped to [-1000, 1000]."""
```

Save it to `/app/calc.py`. The verifier will import `add` and check
`add(2, 3) == 5` AND that the clamp policy holds: `add(900, 900) == 1000`.

The 4 functions you should plan for: `add`, `multiply`, `divide`, `compose`.
Use whatever signatures you think make sense for `divide` and `compose` — you
can always adjust later if the environment changes.
