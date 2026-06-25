Quick change of direction on the calc module in `/app`.

I went over it with the team and we're cutting `divide` and `compose` — nobody
ended up needing them and they're just clutter in the module now. Please take
them out.

What we actually need instead:

- a `subtract(a, b)` operation that works like the other ops
- one entry point I can call by name instead of importing each function:
  `apply_op("add", 2, 3)` should return `5`, `apply_op("subtract", 10, 3)`
  should return `7`, and it should raise `ValueError` if I hand it an op it
  doesn't know
- an `OP_NAMES` list of the supported op names, so I can show them in a menu

All the ground rules we set when we started this module still stand — whatever
conventions the existing operations are supposed to follow, the new code should
follow them too, so the module stays consistent end to end. Keep `/app/PLAN.md`
in step with where the module actually is now.

This is the final step and the only one that counts toward the score.
