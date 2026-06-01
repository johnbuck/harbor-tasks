You have a plan at `/app/plan.md`. Now implement it.

Create `/app/wordfreq.py` so that:

```
python /app/wordfreq.py <file.txt> [--top N] [--min-len L] [--stopwords w1,w2,...]
```

Tokenization (always applied):
- Split on whitespace, lowercase each token, then **strip leading/trailing
  punctuation** (`token.strip(string.punctuation)`). Internal punctuation (the
  apostrophe in `don't`) is kept. Drop tokens that are empty after stripping.

Behavior:
- **Default (no `--top`):** print the single most-common word. **Ties are broken
  alphabetically** (the lowercased word that comes first wins). This must be
  deterministic — do NOT rely on `Counter.most_common(1)` alone, which is
  insertion-order-dependent on ties.
- **`--top N`:** print the top `N` words, one per line, formatted exactly as
  `word count` (single space), ordered by descending count then alphabetically.
- **`--min-len L`:** ignore tokens shorter than `L` characters (after stripping).
- **`--stopwords w1,w2,...`:** comma-separated words to exclude from the counts.

Requirements:
- Use only Python standard library modules (`sys`, `argparse`, `collections`,
  `string`).
- Default output is exactly one line: the word, nothing else.

Examples (given `/app/sample.txt`):
- `python /app/wordfreq.py /app/sample.txt`
  → the single most-common word (alphabetical tie-break).
- `python /app/wordfreq.py /app/sample.txt --top 3`
  → three `word count` lines.
- `python /app/wordfreq.py /app/sample.txt --stopwords the,a,and --min-len 3`
  → most-common word excluding stopwords and short tokens.
