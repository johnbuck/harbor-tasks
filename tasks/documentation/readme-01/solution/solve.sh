#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/README.md <<'EOF'
# greet.py

A simple command-line program that prints a greeting for a given name.

## Usage

```
python greet.py <name> [--times N]
```

## Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | positional | yes | — | The name of the person to greet. |
| `--times N` | option | no | `1` | How many times to print the greeting. Must be at least 1. |

## Examples

Basic greeting:

```
$ python greet.py Alice
Hello, Alice!
```

Repeat the greeting multiple times:

```
$ python greet.py Alice --times 3
Hello, Alice!
Hello, Alice!
Hello, Alice!
```
EOF
