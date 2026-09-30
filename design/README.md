# SolderDemon m68k through-hole mainboard design

![Populated original rosco_m68k Classic v2 board](../images/mainboard-2.1.jpg)

This directory contains the SolderDemon m68k through-hole mainboard design, derived from the original [rosco_m68k](https://github.com/rosco-m68k/rosco_m68k) board. Open the [KiCad project](kicad/solderdemon_m68k.kicad_pro) to inspect the board. The schematics are split into CPU, memory, CPLDs, DUART, reset, and expansion sheets. A [schematic PDF](kicad/solderdemon_m68k.pdf) is included for quick reading.

## Build references

1. Review the [bill of materials](../docs/BOM.md). Its source is the [KiCad CSV export](kicad/solderdemon_m68k.csv); confirm each footprint and package before ordering.
2. Read [jumper and power notes](../docs/JUMPERS.md) before applying power or connecting an SD card.
3. Use the [J3 expansion pinout](../docs/EXPANSION.md) when making an expansion board. **J3** is the expansion connector; **JP3** is the Flash write-enable jumper.
4. Check the KiCad PCB against [CAM outputs](CAMOutputs/) before fabrication. Regenerate Gerbers and drill files after any design change.

## Contents

- **kicad/**: editable schematic sheets, PCB, project, local symbols and footprints, CSV BOM export, and schematic PDF.
- **tools/**: the scripts that turn r2.13 into r2.42 (below).
- **CAMOutputs/**: Gerber layers and drill files.
- **docs/**: [BOM, jumper notes, and expansion pinout](../docs/README.md).

## Revision 2.42: finished CPLD mainboard

r2.42 removes the J6 address/EXPSEL breakout and the J7 SPI CS2 breakout. Their unused copper
branches are pruned and the affected A1/FC2 routes are reconnected. Sixteen narrow VCC bridge
segments are widened from 0.2 to 0.3 mm. The board and all schematic title blocks carry revision
2.42; the crowded UART pin text and obsolete header labels are removed from the silkscreen.

## Revision 2.14: two ATF1502AS instead of four GALs

r2.14 replaces the four ATF22V10C GALs (IC2, IC3, IC5, IC6) with two ATF1502AS-10JU44 CPLDs in
through-hole PLCC-44 sockets, programmed in circuit through the JTAG header **J9**. The logic and
its check are described in [code/pld/cpld](../code/pld/cpld/README.md). Both sockets sit one above
the other where the three glue GALs stood; the old IC2 gap between the CPU and the ROMs is 24.4 mm
and a socket is 24.6 mm. J8, R31, R32 and R16 moved left to make room; the old GAL
decoupling C23-C25 and the DUART's C27/C28 now stand in one column under J9, and C33 is new.

r2.13 was drawn by hand, so r2.42 is an *edit* of it made by scripts, always starting
again from the r2.13 board in git. To rebuild it (KiCad 10, Docker for the fitter):

```sh
K="/c/Program Files/KiCad/10.0/bin"
./code/pld/cpld/build.sh                  # 1. *.pld -> bin/*.jed, pins checked against the source
python design/tools/verify_cpld.py        # 2. CPLDs against the r2.13 GAL fuse maps
python design/tools/cpld_sch.py           # 3. CPLDs sheet of the schematic, from the PIN lines
"$K/python.exe" design/tools/cpld_board.py   # 4. GALs out, sockets/J9/caps in, nets from the schematic
"$K/python.exe" design/tools/cpld_route.py   # 5. routing with KiCadRoutingTools, planes, cleanup
"$K/python.exe" design/tools/remove_access_headers.py # 6. remove J6/J7 and set revision 2.42
"$K/python.exe" design/tools/cpld_route.py --finish     # 7. prune obsolete header branches
"$K/python.exe" design/tools/repair_dangling.py        # 8. remove the remaining old stubs
"$K/python.exe" design/tools/cpld_route.py             # 9. reconnect affected nets
"$K/python.exe" design/tools/repair_dangling.py        # 10. repeat for residual stubs
"$K/python.exe" design/tools/cpld_route.py             # 11. finish the reconnection
"$K/python.exe" design/tools/polish_board.py           # 12. wider VCC bridges, clean silkscreen
"$K/python.exe" design/tools/brand_project.py          # 13. apply SolderDemon m68k project branding
"$K/kicad-cli.exe" pcb drc --schematic-parity design/kicad/solderdemon_m68k.kicad_pcb
```

Steps 5, 9 and 11 use [KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools) from the
workspace's `tools/KiCadRoutingTools` (set `KRT` to use another clone); its logs go to
`design/kicad/routing/`. `design/tools/check_board.py` prints the DRC of any board with its
zones refilled.

The hardware design is licensed under [CERN OHL v1.2](../LICENCE.hardware.txt). The documentation is attributed in the [repository README](../README.md).
