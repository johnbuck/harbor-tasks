#!/bin/bash
set -e
cat > /app/wordfreq.py <<'EOF'
import sys
from collections import Counter

def main():
    path = sys.argv[1]
    with open(path) as f:
        words = f.read().split()
    words = [w.lower() for w in words]
    counter = Counter(words)
    print(counter.most_common(1)[0][0])

if __name__ == "__main__":
    main()
EOF
