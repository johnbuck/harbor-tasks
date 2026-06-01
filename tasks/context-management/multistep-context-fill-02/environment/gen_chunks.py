import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: '65f34746', 2: '9d6fc5c7', 3: 'c1d448ca', 4: '28231e80', 5: '25b1b5db', 6: '4ab38c09', 7: '7fd4d03e', 8: '654693c8', 9: '43dd1f4c', 10: 'fe1a88fd', 11: '3ba114f7', 12: '0f41a399', 13: '1eaf1aef', 14: 'bb7fbc81', 15: '6d57718d', 16: '80b94692', 17: '520c0391', 18: 'b459e236'}
DECOYS = ['84ad8527', '79125e05']
NEEDLE = 'ServerRoom: B12. MasterKeyLocation: Vault 7. CoolantType: R-410A.'
CORRECTION = 'CORRECTION TO IMPORTANT FACTS: the CoolantType stated in document 1 was wrong. The correct CoolantType is R-32 (supersedes R-410A).'
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
