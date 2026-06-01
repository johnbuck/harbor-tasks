Write an implementation plan for a **multi-mode temperature converter** CLI tool.

The program will be `/app/tempconv.py`. When run as:

```
python /app/tempconv.py <mode> <value>
```

it converts a temperature `<value>` according to `<mode>` and prints the result
to **exactly two decimal places** on stdout. The four supported modes are:

- `c2f` — Celsius → Fahrenheit  (`F = C * 9/5 + 32`)
- `f2c` — Fahrenheit → Celsius  (`C = (F - 32) * 5/9`)
- `c2k` — Celsius → Kelvin      (`K = C + 273.15`)
- `k2c` — Kelvin → Celsius      (`C = K - 273.15`)

Hard requirements your plan must account for:

1. **All four modes**, not just `c2f`.
2. Output is rounded to **exactly two decimals** (e.g. `212.00`, `-40.00`, `98.60`).
3. **Absolute-zero validation:** if the converted result is a temperature
   *below absolute zero* (i.e. a Kelvin value < 0, equivalently below -273.15 °C
   or below -459.67 °F), the program must print an error to **stderr** and exit
   with **status code 2** — it must NOT print a number to stdout.
4. **Unknown mode:** if `<mode>` is not one of the four, print an error to
   stderr and exit with status code 2.

Write your numbered plan to `/app/plan.md`. Include at least 4 numbered steps,
and your plan must explicitly mention all four modes, the two-decimal rounding,
and the absolute-zero / unknown-mode error handling with exit code 2.

Do not implement the script yet — only write the plan.
