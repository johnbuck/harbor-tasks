import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: 'MARKER-01-25ec9096', 2: 'MARKER-02-48ba5864', 3: 'MARKER-03-7961c596', 4: 'MARKER-04-57d53498', 5: 'MARKER-05-5fff0226', 6: 'MARKER-06-8c86ba15', 7: 'MARKER-07-60cb5028', 8: 'MARKER-08-fa38b5b7', 9: 'MARKER-09-9da83e08', 10: 'MARKER-10-896aef63', 11: 'MARKER-11-7f4af9f8'}
NEEDLE = 'ProjectCodename: Helios. PrimaryContact: Dr. Vance. LaunchWindow: 2027-Q3.'
# ~19K tokens/chunk: ~3800 lines of ~5-token filler. Marker + needle buried in.
LINE = "log entry {i:05d}: routine telemetry sample alpha bravo charlie delta echo foxtrot golf hotel"
for nn, mk in MARKERS.items():
    lines = []
    for i in range(1050):
        lines.append(LINE.format(i=i))
        if i == 520:
            lines.append(f"   >>> {mk} <<<")
        if nn == 1 and i == 521:
            lines.append(f"   >>> IMPORTANT FACTS: {NEEDLE} <<<")
    open(f"/app/chunks/chunk_{nn:02d}.txt", "w").write("\n".join(lines) + "\n")
print("chunks generated")
