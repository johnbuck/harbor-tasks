#!/bin/bash
# Reference solution — identifies all 8 genuine contradictions, avoids the 2
# distractor near-misses.
set -e

cat > /app/contradictions.md <<'EOF'
# Internal Contradictions — Meridian Retail Group FY2025 Review

## 1. Q3 Revenue Direction
- Executive Summary: "Q3 revenue grew 12% over Q2, marking the second consecutive
  quarter of sequential growth."
- Finance Appendix: "Q3 revenue came in below Q2, declining for the second
  straight quarter."
One says Q3 grew vs Q2; the other says it declined below Q2. Mutually exclusive.

## 2. Gross Margin
- Executive Summary: margin expanded 80 basis points YoY, reaching 41.3%.
- Finance Appendix: full-year gross margin was 39.1%, a contraction of 120 basis
  points YoY.
Both the level (41.3% vs 39.1%) and the direction (+80 bps vs −120 bps) conflict.

## 3. FY2025 Dividend
- Executive Summary: the board "declared a maiden dividend" to be paid Jan 2026.
- Finance Appendix: the board "did not declare any dividend for FY2025."
Cannot have both declared a maiden dividend and declared none.

## 4. Balance-Sheet Cash Position
- Executive Summary: ended the year with $84 million in net cash.
- Finance Appendix: closed the year in a net debt position of $46 million.
Net cash of $84M and net debt of $46M cannot both describe the same year-end.

## 5. Year-End Headcount
- Executive Summary: 5,200 employees, flat year over year.
- Operations Report: 6,050 employees, up ~16% year over year.
The headcount figure and its YoY direction directly conflict.

## 6. Largest Fulfillment Center
- Executive Summary: the Reno, Nevada hub is the company's largest by throughput.
- Operations Report: the Columbus, Ohio hub is the largest by throughput, more
  than Reno and Phoenix combined.
Only one hub can be the largest.

## 7. Customer Acquisition Cost (CAC) Direction
- Executive Summary: CAC fell 6% quarter-over-quarter.
- Operations Report: CAC rose 6% quarter-over-quarter.
CAC cannot have both fallen and risen by 6% in the same quarter.

## 8. CEO Name
- Executive Summary: names the CEO as Dana Whitfield.
- Investor Outlook: names the founder and current CEO as Marcus Whitfield.
The document gives two different names for the current CEO.

---

Note: the "4.7 million members now / 6 million by end of FY2026" pairing is a
current value versus a future target (not a contradiction), and the
"$455–$470M / $420–$435M" Q4 figures are an explicitly-superseded forecast
revision (not a contradiction). Neither is reported above.
EOF
