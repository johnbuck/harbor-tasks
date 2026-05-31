#!/bin/bash
# Oracle: uses ONLY the three correct tools, once each.
set -u
cc=$(csv-row-count /app/customers.csv)
top=$(word-tally /app/notes.txt | awk 'NR==1 {print $2}')
tq=$(json-key-sum /app/orders.json quantity)
python3 -c "
import json
print(json.dumps({'customer_count': int('$cc'), 'top_word': '$top'.lower(), 'total_quantity': int('$tq')}))
" > /app/answer.json
