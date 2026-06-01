Write an implementation plan for a word-frequency CLI tool.

The program will be `/app/wordfreq.py`. Invocation:

```
python /app/wordfreq.py <file.txt> [--top N] [--min-len L] [--stopwords w1,w2,...]
```

Tokenization (applies to every mode):
- Split the file on whitespace and lowercase each token.
- **Strip leading/trailing punctuation** from each token so that `dog,` `"dog"`
  and `dog` all count as the word `dog`. (Internal characters such as the
  apostrophe in `don't` are kept.) Tokens that become empty after stripping are
  discarded.

Behavior:
1. **Default (no `--top`):** print the single most-common word to stdout.
   **Ties are broken alphabetically** — if two words share the top count, print
   the one that is alphabetically first (lowercase). This must be deterministic.
2. **`--top N`:** print the top `N` words, one per line, formatted `word count`,
   ordered by descending count, then alphabetically for ties.
3. **`--min-len L`:** ignore tokens shorter than `L` characters (after stripping).
4. **`--stopwords w1,w2,...`:** comma-separated list of words to exclude from the
   counts entirely.

Write your numbered plan to `/app/plan.md`. Include at least 4 numbered steps,
and your plan must explicitly mention punctuation stripping, the deterministic
**alphabetical tie-break**, `--top`, `--min-len`, and `--stopwords`.

Do not implement the script yet — only write the plan.
