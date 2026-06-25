#!/bin/bash
# Oracle: covers all 8 facts, each stated with the CORRECT value and cited to the
# authoritative page in the same sentence/paragraph. Avoids the press.html and
# drafts.html distractors. The NSF total is the synthesis $4.2M + $1.1M = $5.3M.
cat > /app/brief.md <<'EOF'
# Mirador Labs — research brief

Mirador Labs is a small open-research nonprofit [founded in 2024](/about.html),
headquartered in [San Francisco](/about.html). It runs three active groups —
quantum simulation, climate modeling, and neural systems.

The climate group is led by [Dr. Petra Holm](/people.html). Across its 2025
National Science Foundation awards the lab received a total of
[$5.3 million in NSF funding](/funding.html) — the sum of the
[$4.2 million climate award](/research/climate.html) and the
[$1.1 million neural-systems award](/research/neural.html). (The 2025 quantum
work is funded by a separate DOE grant, and the climate group's earlier $3.0M
NSF award concluded in 2024; neither is part of the 2025 NSF total.)

In 2025 the lab released [18 peer-reviewed or preprint publications](/publications/2025.html),
up from 5 the prior year. It maintains formal research partnerships with
[UCSF, BioGen Therapeutics, and NCAR](/partners.html).

The lab employed [23 full-time staff in 2025](/careers.html) across its three
research groups and operations team, and trains its spiking-network models on an
in-house cluster of [12 NVIDIA H100 GPUs](/research/neural.html).
EOF
