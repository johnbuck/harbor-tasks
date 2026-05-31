#!/bin/bash
# Oracle: writes a brief that covers all 5 required facts with one explicit
# inline citation per fact.
cat > /app/brief.md <<'EOF'
# Mirador Labs — research brief

Mirador Labs is a small open-research nonprofit [founded in 2024](/about.html) and based in San Francisco. The lab runs three active research areas — quantum simulation, climate modeling, and neural systems — and operates with a mix of grant funding and corporate partnerships.

The climate group is led by [Dr. Petra Holm](/people.html). In 2025 the group received a [$4.2 million NSF grant](/research/climate.html) to extend its regional downscaling work. The quantum group, led by Dr. Yusra Chen, produced the lab's first published method (the "Mirador Method") in its founding year and continues to release tooling to PyPI. The neural systems group, led by Dr. Ravi Iyengar, runs work on biologically-plausible spiking networks in partnership with UCSF.

Across all three groups, Mirador Labs published [18 peer-reviewed or preprint papers in 2025](/publications/2025.html), up from 5 the prior year. The lab maintains formal research partnerships with [UCSF, BioGen Therapeutics, and NCAR](/partners.html); BioGen specifically collaborates on small-molecule quantum simulation, and NCAR partners on the climate downscaling work.
EOF
