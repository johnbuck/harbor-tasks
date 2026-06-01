#!/bin/bash
# REVISION TRIGGER: the spec changed mid-task. Stamp a REVISION.md into /app
# announcing the new requirements. The agent must RE-PLAN: their original
# `divide` / `compose` plan is now obsolete; new requirements override it.
# The final verifier grades each revised requirement independently (partial
# credit), so the discrimination is "how cleanly did the harness re-plan?"
# rather than an all-or-nothing pass.

cat > /app/REVISION.md <<'EOF'
# REVISION — requirements changed

After steps 1 and 2 completed, the product team revised the spec. The
remaining planned functions (`divide` and `compose`) are SCRAPPED. The new,
final spec for `/app/calc.py` is:

KEEP (already implemented in steps 1-2):
  1. add(a: int, b: int) -> int        — returns a + b
  2. multiply(a: int, b: int) -> int   — returns a * b

ADD (new):
  3. subtract(a: int, b: int) -> int   — returns a - b
  4. apply_op(op: str, a: int, b: int) -> int
       — dispatches to add / multiply / subtract based on `op`.
         Raise ValueError on any unknown op.
  5. OP_NAMES: a module-level list (or tuple) of the three supported op
       names, exactly ["add", "multiply", "subtract"] (order matters).

NO LONGER IN THE SPEC:
  - `divide` and `compose` are not part of the new spec.
EOF
rm -- "$0"
