Create `/app/linecount.py` — a command-line line/character counting tool
(a small `wc`-style utility).

## Behavior

### Single file (line mode — default)

`python /app/linecount.py <file>` prints ONLY the integer line count of `<file>`
to stdout (nothing else, then a newline).

- An empty file prints `0`.
- A line is any record terminated by `\n`. **A final line that is NOT terminated
  by a newline still counts as a line.** So a file whose contents are exactly
  `"a\nb"` (no trailing newline) has a line count of `2`, and `"a\nb\n"` also has
  a line count of `2`.

### Character mode

`python /app/linecount.py -c <file>` (or `--chars`) prints the number of
characters in `<file>` instead of lines. (`-c` counts every byte, including
newlines.)

### Multiple files

When two or more files are given, print one line per file in the form
`<count> <filename>` (count, a single space, the filename as passed on the
command line), and then a final line `<total> total` with the summed count.
This works in both line mode and `-c` mode.

Example (`a.txt` has 3 lines, `b.txt` has 4 lines):

```
3 a.txt
4 b.txt
7 total
```

### Standard input

When NO file argument is given, read from standard input and print the count
(line or `-c` char mode) of the piped data.

### Errors

If a named file does not exist, print an error message to **stderr** (not stdout)
and exit with a **non-zero** status. Do not print a Python traceback. With
multiple files, a missing file must not prevent the other files from being
counted (still exit non-zero overall).

## Constraints

- Single-file success prints ONLY the integer (no labels, no extra text).
- Exit 0 on success; non-zero when any named file is missing.
