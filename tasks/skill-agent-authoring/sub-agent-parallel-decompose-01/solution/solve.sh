#!/bin/bash
# Oracle: writes the known integer answer for each problem to /app/out/NN.txt.
# Self-contained (answers baked inline) so it does not depend on solution/ being
# mounted. The agent NEVER sees these — the real-run container has no answer key.
# Regenerate together with problems/ + tests/answers.json via solution/gen.py.
set -u
mkdir -p /app/out

echo 215 > /app/out/01.txt
echo 180 > /app/out/02.txt
echo 119 > /app/out/03.txt
echo 128 > /app/out/04.txt
echo 29 > /app/out/05.txt
echo 184 > /app/out/06.txt
echo 140 > /app/out/07.txt
echo 112 > /app/out/08.txt
echo 153 > /app/out/09.txt
echo 133 > /app/out/10.txt
echo 111 > /app/out/11.txt
echo 169 > /app/out/12.txt
echo 131 > /app/out/13.txt
echo 52 > /app/out/14.txt
echo 114 > /app/out/15.txt
echo 56 > /app/out/16.txt
echo 81 > /app/out/17.txt
echo 142 > /app/out/18.txt
echo 183 > /app/out/19.txt
echo 99 > /app/out/20.txt
echo 60 > /app/out/21.txt
echo 113 > /app/out/22.txt
echo 99 > /app/out/23.txt
echo 110 > /app/out/24.txt
echo 113 > /app/out/25.txt
echo 75 > /app/out/26.txt
echo 160 > /app/out/27.txt
echo 136 > /app/out/28.txt
echo 129 > /app/out/29.txt
echo 135 > /app/out/30.txt
echo 91 > /app/out/31.txt
echo 173 > /app/out/32.txt
echo 51 > /app/out/33.txt
echo 201 > /app/out/34.txt
echo 63 > /app/out/35.txt
echo 195 > /app/out/36.txt
echo 161 > /app/out/37.txt
echo 44 > /app/out/38.txt
echo 103 > /app/out/39.txt
echo 210 > /app/out/40.txt
echo 38 > /app/out/41.txt
echo 65 > /app/out/42.txt
echo 166 > /app/out/43.txt
echo 156 > /app/out/44.txt
echo 134 > /app/out/45.txt
echo 82 > /app/out/46.txt
echo 102 > /app/out/47.txt
echo 115 > /app/out/48.txt
echo 77 > /app/out/49.txt
echo 192 > /app/out/50.txt
echo 91 > /app/out/51.txt
echo 51 > /app/out/52.txt
echo 92 > /app/out/53.txt
echo 54 > /app/out/54.txt
echo 155 > /app/out/55.txt
echo 178 > /app/out/56.txt
echo 26 > /app/out/57.txt
echo 106 > /app/out/58.txt
echo 96 > /app/out/59.txt
echo 73 > /app/out/60.txt
