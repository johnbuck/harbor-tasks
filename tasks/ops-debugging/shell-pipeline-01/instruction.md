There is an Nginx-style access log at `/app/access.log`. Each line looks like:

```
<ip> - - [<time>] "GET /path HTTP/1.1" <status> <bytes>
```

Find the single IP address responsible for the **most HTTP 500 responses**.
Write **only that IP address** (no extra text, no trailing punctuation) to
`/app/answer.txt`.

Constraints:

- Do not modify `/app/access.log`.
- `/app/answer.txt` must contain just the IP address.
