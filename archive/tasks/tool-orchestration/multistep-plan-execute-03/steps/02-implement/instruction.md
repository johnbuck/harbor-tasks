You have a plan at `/app/plan.md`. Now implement it.

Create `/app/tempconv.py` so that:

```
python /app/tempconv.py <mode> <value>
```

converts `<value>` per `<mode>` and prints the result to **exactly two decimal
places** with no extra text.

Modes and formulas:
- `c2f` — Celsius → Fahrenheit:  `F = C * 9/5 + 32`
- `f2c` — Fahrenheit → Celsius:  `C = (F - 32) * 5/9`
- `c2k` — Celsius → Kelvin:      `K = C + 273.15`
- `k2c` — Kelvin → Celsius:      `C = K - 273.15`

Examples:
- `python /app/tempconv.py c2f 100` → `212.00`
- `python /app/tempconv.py c2f -40` → `-40.00`
- `python /app/tempconv.py f2c 98.6` → `37.00`
- `python /app/tempconv.py c2k 0`   → `273.15`
- `python /app/tempconv.py k2c 0`   → `-273.15`

Requirements:
- Use only Python standard library modules (`sys`).
- Output must be **exactly two decimal places** (use `f"{value:.2f}"`).
- **Absolute-zero guard:** if the input describes a temperature below absolute
  zero (Kelvin < 0, i.e. below -273.15 °C or below -459.67 °F), do NOT print a
  number — write an error to **stderr** and exit with status code **2**.
  Example: `python /app/tempconv.py c2k -300` must exit 2 (and print nothing to
  stdout), because -300 °C is below absolute zero.
- **Unknown mode:** if `<mode>` is not one of the four, write an error to
  **stderr** and exit with status code **2**.
- A successful conversion exits with status code **0**.
