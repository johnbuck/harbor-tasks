You have a plan at `/app/plan.md`. Now implement it.

Create `/app/wordfreq.py` so that:

```
python /app/wordfreq.py <file.txt>
```

reads the text file, splits on whitespace, lowercases every token, counts frequencies, and prints the single most-common word to stdout (just the word, one line, no extra output).

Requirements:
- Use only Python standard library modules (`sys`, `collections`).
- If there is a tie, printing any one of the tied words is acceptable.
