Review the pull request diff at `/app/change.diff`.

Write `/app/review.md` with your code review. Your review should:

- Identify every real issue in the diff — correctness problems, security
  vulnerabilities (injection, sensitive-data exposure, broken access control),
  or API misuse. The diff contains more than one genuine issue.
- For each issue, name the specific symbol/endpoint affected and recommend a
  concrete fix.
- Do not rubber-stamp: if there is a meaningful problem, you must flag it.
- Do not invent problems. Not everything that *looks* suspicious is a real bug —
  flagging a non-issue as a vulnerability counts against you. Only raise issues
  you can justify from the diff.
- Do not pad the review with trivial nitpicks (style, variable naming, minor
  whitespace).

Write only the review to `/app/review.md`. Do not add commentary outside the file.
