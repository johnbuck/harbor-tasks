import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: 'MARKER-01-65f34746', 2: 'MARKER-02-9d6fc5c7', 3: 'MARKER-03-c1d448ca', 4: 'MARKER-04-28231e80', 5: 'MARKER-05-25b1b5db', 6: 'MARKER-06-4ab38c09', 7: 'MARKER-07-7fd4d03e', 8: 'MARKER-08-654693c8', 9: 'MARKER-09-43dd1f4c', 10: 'MARKER-10-fe1a88fd', 11: 'MARKER-11-3ba114f7'}
NEEDLE = 'ServerRoom: B12. MasterKeyLocation: Vault 7. CoolantType: R-410A.'
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
