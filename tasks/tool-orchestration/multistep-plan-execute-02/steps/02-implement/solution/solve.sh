#!/bin/bash
set -e
cat > /app/wordfreq.py <<'EOF'
import argparse
import string
from collections import Counter


def tokenize(text):
    out = []
    for raw in text.split():
        w = raw.lower().strip(string.punctuation)
        if w:
            out.append(w)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--top", type=int, default=None)
    ap.add_argument("--min-len", type=int, default=0, dest="min_len")
    ap.add_argument("--stopwords", default="")
    args = ap.parse_args()

    stop = {w for w in args.stopwords.split(",") if w}
    with open(args.file) as f:
        words = tokenize(f.read())
    words = [w for w in words if len(w) >= args.min_len and w not in stop]

    counts = Counter(words)
    # Deterministic ordering: by descending count, then alphabetically.
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    if args.top is not None:
        for word, n in ranked[:args.top]:
            print(f"{word} {n}")
    else:
        if ranked:
            print(ranked[0][0])


if __name__ == "__main__":
    main()
EOF
