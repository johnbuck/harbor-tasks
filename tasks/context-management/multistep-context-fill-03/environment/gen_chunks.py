import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: 'MARKER-01-ff82c4be', 2: 'MARKER-02-fc02dce8', 3: 'MARKER-03-423c1bd0', 4: 'MARKER-04-537a41d3', 5: 'MARKER-05-0478efaa', 6: 'MARKER-06-323f111f', 7: 'MARKER-07-b940a57c', 8: 'MARKER-08-6f4a1c6d', 9: 'MARKER-09-da31711d', 10: 'MARKER-10-c1944814', 11: 'MARKER-11-2116526c'}
NEEDLE = 'VaultPin: 8842. BackupCourier: Meridian Logistics. RetentionYears: 12.'
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
