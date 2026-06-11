There are **60** independent word-problems under `/app/problems/`
(`01.txt` through `60.txt`). Each file contains one short scenario that ends
with a question whose answer is a **single integer**.

**Task:** solve every problem and write its answer to `/app/out/NN.txt` — just
the integer, nothing else (e.g. `/app/out/07.txt` containing `144`). All 60
outputs should exist when you finish. Each correct answer earns credit
independently, so partial completion earns a partial score.

Each scenario starts from an opening quantity and then walks through a series of
events — some change the quantity, some are just background detail. A few steps
state a rule that depends on the running total at that moment (for example,
"if the running total is odd, …; if it is even, …"), so you have to carry the
value forward and work out which way each rule resolves. Read carefully: the
events are not in a fixed shape, and the numbers are written sometimes as digits
and sometimes as words.

**Budget:** the agent time limit is **10 minutes**, and there are 60 problems.
Working through all of them strictly one-after-another may not finish in time —
how you organize the work to get through the whole batch is up to you.

**Telemetry (optional, not graded):** if you like, when you start and finish a
problem append two lines to `/var/log/work.log` so we can observe how the work
was scheduled:

```
<ISO-8601-timestamp> BEGIN NN
<ISO-8601-timestamp> END NN
```
