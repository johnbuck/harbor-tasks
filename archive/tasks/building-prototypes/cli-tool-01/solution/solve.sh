#!/bin/bash
# Reference solution — a small wc-style line/char counter.
set -e

cat > /app/linecount.py <<'EOF'
import sys


def count(data, chars):
    if chars:
        return len(data)
    # A final line without a trailing newline still counts.
    n = data.count(b"\n")
    if data and not data.endswith(b"\n"):
        n += 1
    return n


def main(argv):
    chars = False
    files = []
    for a in argv:
        if a in ("-c", "--chars"):
            chars = True
        else:
            files.append(a)

    # No files: read stdin.
    if not files:
        data = sys.stdin.buffer.read()
        print(count(data, chars))
        return 0

    status = 0
    results = []
    for path in files:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            print(f"linecount: {path}: {e.strerror}", file=sys.stderr)
            status = 1
            continue
        results.append((count(data, chars), path))

    if len(files) == 1:
        # Single named file: print only the integer on success; on failure the
        # error already went to stderr and we print nothing to stdout.
        if results:
            print(results[0][0])
        return status

    # Two or more named files: per-file lines + a total (over the files that
    # were readable).
    total = 0
    for c, path in results:
        print(f"{c} {path}")
        total += c
    print(f"{total} total")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
EOF
