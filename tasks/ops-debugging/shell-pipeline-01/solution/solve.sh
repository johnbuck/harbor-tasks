#!/bin/bash
# Reference solution — used by the `oracle` agent for sanity-checking the task.
# Each sub-result is computed with a small awk program. The log fields are:
#   $1=ip  ...  $6="<METHOD  ($7=<path>  $8=HTTP/1.1")  $9=status  $10=bytes
# but quoting splits the request across $6..$8, so we anchor on field positions
# from the end where it matters and parse the quoted request explicitly.
set -e

LOG=/app/access.log

# --- TOP_500_IP: most 500s, tie-break by total request volume, then IP asc ----
top_500_ip=$(awk '
  { vol[$1]++ }                                   # total requests per IP
  $9 == 500 { c500[$1]++ }                        # status is field 9
  END {
    for (ip in c500) {
      v = vol[ip]
      # sort key: count desc, volume desc, ip asc
      printf "%010d %010d %s\n", c500[ip], v, ip
    }
  }' "$LOG" | sort -k1,1nr -k2,2nr -k3,3 | head -1 | awk '{print $3}')

# --- TOTAL_5XX: count of all 5xx lines ---------------------------------------
total_5xx=$(awk '$9 >= 500 && $9 <= 599 {n++} END {print n+0}' "$LOG")

# --- DISTINCT_5XX_IPS ---------------------------------------------------------
distinct_5xx=$(awk '$9 >= 500 && $9 <= 599 {seen[$1]=1} END {print length(seen)}' "$LOG")

# --- TOP_4XX_PATH: most-requested path among 4xx, query stripped, tie -> asc --
top_4xx_path=$(awk '
  $9 >= 400 && $9 <= 499 {
    p = $7
    sub(/\?.*/, "", p)
    cnt[p]++
  }
  END { for (p in cnt) printf "%010d %s\n", cnt[p], p }' "$LOG" \
  | sort -k1,1nr -k2,2 | head -1 | awk '{print $2}')

# --- TOTAL_2XX_BYTES: sum bytes over 2xx, "-" counts as 0 --------------------
total_2xx_bytes=$(awk '$9 >= 200 && $9 <= 299 { b = ($10 == "-" ? 0 : $10); s += b } END {print s+0}' "$LOG")

cat > /app/answer.txt <<EOF
TOP_500_IP=${top_500_ip}
TOTAL_5XX=${total_5xx}
DISTINCT_5XX_IPS=${distinct_5xx}
TOP_4XX_PATH=${top_4xx_path}
TOTAL_2XX_BYTES=${total_2xx_bytes}
EOF
