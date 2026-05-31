You are building a small Python module `/app/calc.py` over the next 4 steps.

**Before writing any code**, write a short plan to `/app/PLAN.md` describing
the 4 functions you'll implement (function names, expected signatures,
expected behavior). Treat this as a one-time plan you'll execute step by step.

Then **for this step (step 1)**, implement just the first function:

```python
def add(a: int, b: int) -> int:
    """Return a + b."""
```

Save it to `/app/calc.py`. The verifier will import `add` from `/app/calc.py`
and check `add(2, 3) == 5`.

The 4 functions you should plan for: `add`, `multiply`, `divide`, `compose`.
Use whatever signatures you think make sense for `divide` and `compose` — you
can always adjust later if the environment changes.
