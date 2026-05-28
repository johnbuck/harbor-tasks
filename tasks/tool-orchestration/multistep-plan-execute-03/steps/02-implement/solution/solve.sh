#!/bin/bash
set -e
cat > /app/c2f.py <<'EOF'
import sys

def celsius_to_fahrenheit(c):
    return c * 9 / 5 + 32

def main():
    celsius = float(sys.argv[1])
    fahrenheit = celsius_to_fahrenheit(celsius)
    print(f"{fahrenheit:.1f}")

if __name__ == "__main__":
    main()
EOF
