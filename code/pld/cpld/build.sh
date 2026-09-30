#!/usr/bin/env bash
# Build the two ATF1502AS of rosco_m68k classic THT r2.14: *.pld -> bin/*.jed
#
# Uses the WinCUPL + Atmel fitter docker image (see ../../../../tools/cpld-toolchain), then checks
# that the fitter kept every pin where the .pld puts it -- the board is routed to those pins.
#
#   ./build.sh            (needs a running docker)
#
# Program the .jed over JTAG (J9, chain TDI -> IC2 -> IC3 -> TDO), e.g. with an ATDH1150USB or
# an FT232H under OpenOCD; the TL866 cannot program the ATF150x.
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1
IMAGE=${CPLD_IMAGE:-dinoboards/cpld-toolchain:latest}
HOSTDIR=$(pwd -W 2>/dev/null || pwd)

rm -rf bin
for f in ic2_decoder ic3_glue; do
    docker run --rm -v "$HOSTDIR:/work" "$IMAGE" cupld "$f" > /dev/null 2>&1 || true
    [ -f "bin/$f.jed" ] || { echo "$f: no .jed, see bin/$f.fit"; exit 1; }
    python - "$f" <<'EOF'
import re, sys
f = sys.argv[1]
src = re.sub(r'/\*.*?\*/', ' ', open(f + '.pld').read(), flags=re.S)
want = {s: int(n) for n, s in re.findall(r'^\s*PIN\s+(\d+)\s*=\s*(\w+)\s*;', src, flags=re.M)}
fit = open('bin/' + f + '.fit', encoding='latin-1').read()
got = {s: int(n) for s, n in re.findall(r'^(\w+) is placed at pin (\d+)', fit, flags=re.M)}
got.update({s: int(n) for s, n in re.findall(r'^(\w+) assigned to pin\s+(\d+)', fit, flags=re.M)})
bad = {s: (n, got.get(s)) for s, n in want.items() if got.get(s) != n}
assert not bad, f'{f}: fitter moved pins {bad}'
used = re.search(r'Total Macro cells used\s+(\S+)', fit).group(1)
print(f'{f}: {len(want)} pins as assigned, {used} macrocells')
EOF
done
