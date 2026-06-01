import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: 'ff82c4be', 2: 'fc02dce8', 3: '423c1bd0', 4: '537a41d3', 5: '0478efaa', 6: '323f111f', 7: 'b940a57c', 8: '6f4a1c6d', 9: 'da31711d', 10: 'c1944814', 11: '2116526c', 12: '8b17075d', 13: '2b55c626', 14: '03fd9a32', 15: 'c34032b5', 16: '3b9db9d1', 17: '4d9ceef6', 18: '93cb2420'}
DECOYS = ['30e9d4da', '413b3c9c']
NEEDLE = 'VaultPin: 8842. BackupCourier: Meridian Logistics. RetentionYears: 12.'
CORRECTION = 'CORRECTION TO IMPORTANT FACTS: the RetentionYears stated in document 1 was wrong. The correct RetentionYears is 7 (supersedes 12).'
TRAP_CHUNK = 14
DECOY_CHUNK = 16
# ~19K tokens/chunk: ~1050 lines of ~14-token filler. Marker + needle buried in.
LINE = "log entry {i:05d}: routine telemetry sample alpha bravo charlie delta echo foxtrot golf hotel"
for nn, mk in MARKERS.items():
    marker = "MARKER-%02d-%s" % (nn, mk)
    lines = []
    if nn == DECOY_CHUNK:
        lines.append("=== DRAFT - DO NOT RECORD ===")
        lines.append("The following two marker codes are DRAFT placeholders and must")
        lines.append("NOT be recalled or listed in your final answer. Ignore them:")
        lines.append("   >>> MARKER-D1-%s <<<" % DECOYS[0])
        lines.append("   >>> MARKER-D2-%s <<<" % DECOYS[1])
        lines.append("=== END DRAFT BLOCK ===")
    for i in range(1050):
        lines.append(LINE.format(i=i))
        if i == 520:
            lines.append("   >>> %s <<<" % marker)
        if nn == 1 and i == 521:
            lines.append("   >>> IMPORTANT FACTS: %s <<<" % NEEDLE)
        if nn == TRAP_CHUNK and i == 521:
            lines.append("   >>> %s <<<" % CORRECTION)
    open("/app/chunks/chunk_%02d.txt" % nn, "w").write("\n".join(lines) + "\n")
print("chunks generated")
