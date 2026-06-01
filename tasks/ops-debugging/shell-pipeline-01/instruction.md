There is an Nginx-style access log at `/app/access.log`. Each line looks like:

```
<ip> - - [<time>] "<METHOD> <path> HTTP/1.1" <status> <bytes>
```

Note: the `<bytes>` field may be a literal `-` (dash) meaning "no body / zero
bytes". The `<path>` may contain a `?query` string.

Compute the following and write them to `/app/answer.txt`, **one per line**, in
**exactly** this `KEY=value` format (keys in this order, no extra lines, no extra
whitespace, no trailing punctuation):

```
TOP_500_IP=<ip>
TOTAL_5XX=<count>
DISTINCT_5XX_IPS=<count>
TOP_4XX_PATH=<path>
TOTAL_2XX_BYTES=<sum>
```

Definitions:

- `TOP_500_IP` — the IP with the **most HTTP `500`** responses (exactly status
  `500`, not other 5xx). **If two or more IPs tie on `500` count, break the tie
  by choosing the IP with the larger total number of requests in the log** (all
  statuses). If still tied, choose the lexicographically smallest IP.
- `TOTAL_5XX` — total number of requests whose status is in the `5xx` range
  (`500`–`599` inclusive), counting every matching line.
- `DISTINCT_5XX_IPS` — the number of **distinct** IPs that produced at least one
  `5xx` response.
- `TOP_4XX_PATH` — the most-requested URL **path** among `4xx` (`400`–`499`)
  responses, with any `?query` string **stripped** (so `/search?q=foo+bar`
  counts as `/search`). On a tie, choose the lexicographically smallest path.
- `TOTAL_2XX_BYTES` — the sum of the `<bytes>` field over all `2xx`
  (`200`–`299`) responses, treating a `-` byte field as `0`.

Constraints:

- Do not modify `/app/access.log`.
- `/app/answer.txt` must contain exactly the five `KEY=value` lines above.

Each `KEY=value` line is graded independently — a partly-correct answer scores a
fraction.
