#!/bin/bash
set -e
cat > /app/tempconv.py <<'EOF'
import sys

MODES = ("c2f", "f2c", "c2k", "k2c")


def to_kelvin(mode, value):
    """Kelvin equivalent of the INPUT value (for the absolute-zero guard)."""
    if mode in ("c2f", "c2k"):   # input is Celsius
        return value + 273.15
    if mode == "f2c":            # input is Fahrenheit
        return (value - 32) * 5 / 9 + 273.15
    return value                 # k2c: input is Kelvin


def convert(mode, value):
    if mode == "c2f":
        return value * 9 / 5 + 32
    if mode == "f2c":
        return (value - 32) * 5 / 9
    if mode == "c2k":
        return value + 273.15
    if mode == "k2c":
        return value - 273.15
    raise KeyError(mode)


def main():
    if len(sys.argv) != 3:
        print("usage: tempconv.py <mode> <value>", file=sys.stderr)
        sys.exit(2)
    mode, raw = sys.argv[1], sys.argv[2]
    if mode not in MODES:
        print(f"error: unknown mode {mode!r}", file=sys.stderr)
        sys.exit(2)
    value = float(raw)
    # Absolute-zero guard: input below 0 K is physically impossible.
    if to_kelvin(mode, value) < -1e-9:
        print("error: temperature below absolute zero", file=sys.stderr)
        sys.exit(2)
    print(f"{convert(mode, value):.2f}")


if __name__ == "__main__":
    main()
EOF
