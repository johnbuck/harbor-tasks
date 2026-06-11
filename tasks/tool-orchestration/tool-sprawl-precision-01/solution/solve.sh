#!/bin/bash
# Oracle: select the three correct tools (found by reading --help, not by name),
# invoking each exactly once. The names give nothing away; only the descriptions
# do — recstat (data-row count), lexrank (top word), colroll (field sum).
set -u
cc=$(recstat /app/customers.csv)
top=$(lexrank /app/notes.txt)
tq=$(colroll /app/orders.json quantity)
python3 -c "
import json
print(json.dumps({'customer_count': int('$cc'), 'top_word': '$top'.lower(), 'total_quantity': int('$tq')}))
" > /app/answer.json
