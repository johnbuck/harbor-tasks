import os
os.makedirs("/app/chunks", exist_ok=True)
MARKERS = {1: '25ec9096', 2: '48ba5864', 3: '7961c596', 4: '57d53498', 5: '5fff0226', 6: '8c86ba15', 7: '60cb5028', 8: 'fa38b5b7', 9: '9da83e08', 10: '896aef63', 11: '7f4af9f8', 12: 'fdb6ba57', 13: '6a5479cd', 14: 'ccffd399', 15: '9dc71ea9', 16: '8aa6f206', 17: '4231e66c', 18: 'ae12be76'}
DECOYS = ['21ff7951', '55e7694b']
NEEDLE = 'ProjectCodename: Helios. PrimaryContact: Dr. Vance. LaunchWindow: 2027-Q3.'
CORRECTION = 'CORRECTION TO IMPORTANT FACTS: the LaunchWindow stated in document 1 was wrong. The correct LaunchWindow is 2027-Q4 (supersedes 2027-Q3).'
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
