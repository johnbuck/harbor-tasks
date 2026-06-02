#!/bin/bash
# Oracle: writes the known integer answer for each problem to /app/out/NN.txt.
# Self-contained (answers baked inline) so it does not depend on solution/ being
# mounted. The agent NEVER sees these — the real-run container has no answer key.
set -u
mkdir -p /app/out

echo 91 > /app/out/01.txt
echo 87 > /app/out/02.txt
echo 144 > /app/out/03.txt
echo 96 > /app/out/04.txt
echo 185 > /app/out/05.txt
echo 47 > /app/out/06.txt
echo 51 > /app/out/07.txt
echo 62 > /app/out/08.txt
echo 69 > /app/out/09.txt
echo 113 > /app/out/10.txt
echo 96 > /app/out/11.txt
echo 40 > /app/out/12.txt
echo 94 > /app/out/13.txt
echo 79 > /app/out/14.txt
echo 165 > /app/out/15.txt
echo 88 > /app/out/16.txt
echo 188 > /app/out/17.txt
echo 66 > /app/out/18.txt
echo 54 > /app/out/19.txt
echo 81 > /app/out/20.txt
echo 63 > /app/out/21.txt
echo 114 > /app/out/22.txt
echo 99 > /app/out/23.txt
echo 41 > /app/out/24.txt
echo 106 > /app/out/25.txt
echo 80 > /app/out/26.txt
echo 168 > /app/out/27.txt
echo 107 > /app/out/28.txt
echo 191 > /app/out/29.txt
echo 58 > /app/out/30.txt
echo 57 > /app/out/31.txt
echo 73 > /app/out/32.txt
echo 75 > /app/out/33.txt
echo 106 > /app/out/34.txt
echo 102 > /app/out/35.txt
echo 60 > /app/out/36.txt
echo 109 > /app/out/37.txt
echo 99 > /app/out/38.txt
echo 162 > /app/out/39.txt
echo 108 > /app/out/40.txt
echo 33 > /app/out/41.txt
echo 59 > /app/out/42.txt
echo 60 > /app/out/43.txt
echo 74 > /app/out/44.txt
echo 78 > /app/out/45.txt
echo 125 > /app/out/46.txt
echo 95 > /app/out/47.txt
echo 52 > /app/out/48.txt
echo 112 > /app/out/49.txt
echo 91 > /app/out/50.txt
echo 183 > /app/out/51.txt
echo 100 > /app/out/52.txt
echo 36 > /app/out/53.txt
echo 78 > /app/out/54.txt
echo 63 > /app/out/55.txt
echo 93 > /app/out/56.txt
echo 72 > /app/out/57.txt
echo 126 > /app/out/58.txt
echo 107 > /app/out/59.txt
echo 53 > /app/out/60.txt
