You are building a small Python calculator module `/app/calc.py` over the next
few steps.

**Before writing any code**, write a short plan to `/app/PLAN.md` describing the
four operations you'll implement (names, signatures, expected behavior) and the
dispatch design below. Treat this as a one-time plan you execute step by step.

**Project-wide rule (decided now, at kickoff — applies to EVERY arithmetic
operation in this module, now and forever):** every numeric result must be
**clamped to the inclusive range [-1000, 1000]**. A value above 1000 becomes
1000; a value below -1000 becomes -1000. Implement this once as a shared helper
(`_clamp`) so every operation applies the identical policy. Record this rule in
your PLAN.md so the decision isn't lost.

The four operations to plan for: `add`, `multiply`, `divide`, `compose`.

We also want a **name-based dispatch layer** from the start so new operations
just plug in:

- a module-level `REGISTRY` dict mapping each op name (e.g. `"add"`) to its
  function, and
- a `dispatch(op, *args)` entry point that looks the op up in `REGISTRY`, calls
  it, and raises `ValueError` on an unknown op.

**For this step (step 1)**, implement the clamp helper plus the first two
operations and wire them into the registry/dispatch:

```python
def add(a, b):       # a + b, clamped
def divide(a, b):    # integer division a // b, clamped; ValueError on b == 0
```

Register `add` and `divide` in `REGISTRY` and make `dispatch("add", 2, 3)`
work. Save everything to `/app/calc.py`. The verifier will import the module and
check `add(2, 3) == 5`, the clamp policy (`add(900, 900) == 1000`), `divide`,
`dispatch`, and that `PLAN.md` exists.
