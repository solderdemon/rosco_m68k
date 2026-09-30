# SolderDemon m68k through-hole mainboard design

![Assembled r2.42 mainboard, the GAL version this board grew from](../images/mainboard-r2.42.jpg)

This directory contains the SolderDemon m68k through-hole mainboard design, derived from the original [rosco_m68k](https://github.com/rosco-m68k/rosco_m68k) board. Open the [KiCad project](kicad/solderdemon_m68k.kicad_pro) to inspect the board. The schematics are split into CPU, memory, CPLDs, DUART, reset, and expansion sheets. A [schematic PDF](kicad/solderdemon_m68k.pdf) is included for quick reading.

## Build references

1. Review the [bill of materials](../docs/BOM.md). Its source is the [KiCad CSV export](kicad/solderdemon_m68k.csv); confirm each footprint and package before ordering.
2. Read [jumper and power notes](../docs/JUMPERS.md) before applying power or connecting an SD card.
3. Use the [J3 expansion pinout](../docs/EXPANSION.md) when making an expansion board. **J3** is the expansion connector; **JP3** is the Flash write-enable jumper.
4. Check the KiCad PCB against [CAM outputs](CAMOutputs/) before fabrication. Regenerate Gerbers and drill files after any design change.

## Contents

- **kicad/**: editable schematic sheets, PCB, project, local symbols and footprints, CSV BOM export, and schematic PDF.
- **tools/**: the scripts that turn r2.13 into r1 (below).
- **CAMOutputs/**: Gerber layers and drill files.
- **docs/**: [BOM, jumper notes, and expansion pinout](../docs/README.md).

## r1: SolderDemon numbering, the DUART in the CPLD column

From here on the board carries its own revision numbers, starting at **r1**; the r2.x numbers
below are the rosco_m68k history it grew from.

r1 puts the three PLCC-44 sockets in one column: IC3 (glue), IC2 (decoder) and the DUART IC4
under them. IC4 used to sit 8 mm to the right, and moving it left would have put its pins on the
RAM U4, so the board is 5 mm longer instead (165 × 100 mm). `tools/r1_layout.py` stretches the
r2.42 board along a cut between the CPLDs and the CPU/RAM: everything right of the cut moves 5 mm
right, tracks crossing the cut get a horizontal bridge, so no clearance shrinks. IC4 then moves
into the column, its decoupling cap C22 into the space it left, and the DUART is routed again.
The upstream badges (WEEE bin, OSHW block, rosco_m68k logos, GitHub URL) are gone from the
silkscreen (`tools/strip_silk.py`). The CPU decoupling C20/C12/C29/C31 stands in an even column in the gap the stretch
opened, and the back carries the SolderDemon identity as on the busboard: the logo, the name and
"M68K Computer r1" (`tools/r1_identity.py`). All silkscreen text is in KiCad's own font; the
Futura that r2.x asked for is not installed and made KiCad stop at a message box.

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
python design/tools/strip_silk.py                      # 14. upstream badges off the silkscreen
"$K/python.exe" design/tools/r1_layout.py              # 15. r1: longer board, DUART into the column
"$K/python.exe" design/tools/cpld_route.py             # 16. route the DUART again
"$K/python.exe" design/tools/trim_stubs.py             # 17. cut router overshoots back to their junctions
python design/tools/make_logo.py 17                    # 18. SolderDemon logo footprint, as on the busboard
"$K/python.exe" design/tools/r1_identity.py            # 19. CPU decoupling column, SolderDemon identity on the back
"$K/python.exe" design/tools/cpld_route.py             # 20. route what the column tore up
"$K/python.exe" design/tools/trim_stubs.py             # 21. and trim again
"$K/kicad-cli.exe" pcb drc --schematic-parity design/kicad/solderdemon_m68k.kicad_pcb
```

Steps 5, 9 and 11 use [KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools) from the
workspace's `tools/KiCadRoutingTools` (set `KRT` to use another clone); its logs go to
`design/kicad/routing/`. `design/tools/check_board.py` prints the DRC of any board with its
zones refilled.

The hardware design is licensed under [CERN OHL v1.2](../LICENCE.hardware.txt). The documentation is attributed in the [repository README](../README.md).
