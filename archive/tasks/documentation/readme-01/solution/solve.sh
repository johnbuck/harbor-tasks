#!/bin/bash
# Reference solution — scores 1.0 under the deterministic graded verifier.
set -e

cat > /app/README.md <<'EOF'
# greet.py

A simple command-line program that prints a greeting for one or more given names.

## Usage

```
python greet.py NAME [NAME ...] [--times N] [--greeting WORD] [--shout]
```

## Arguments

| Argument | Kind | Default | Description |
|----------|------|---------|-------------|
| `name` | positional (one or more) | — | One or more names of the people to greet. Accepts multiple names. |
| `--times N` | option | `1` | How many times to print each greeting (default: 1). |
| `--greeting WORD` | option | `Hello` | The greeting word to use (default: Hello). |
| `--shout` | flag | off | Print the greeting in uppercase. |

The program prints one line per greeting in the form `<greeting>, <name>!`.

## Examples

Basic greeting:

```
$ python greet.py Alice
Hello, Alice!
```

Multiple names, repeated, with a custom greeting:

```
$ python greet.py Alice Bob --times 2 --greeting Hi
Hi, Alice!
Hi, Alice!
Hi, Bob!
Hi, Bob!
```

Shout:

```
$ python greet.py Alice --shout
HELLO, ALICE!
```
EOF
