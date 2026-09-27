# Through-hole mainboard design

![Populated Classic v2 board](../../images/mainboard-2.1.jpg)

The through-hole board files live in this upstream R2 directory. Open the [KiCad project](kicad/rosco_m68k.kicad_pro) to inspect or edit the board. The schematics are split into CPU, memory, GALs, DUART, reset, and expansion sheets. A [schematic PDF](kicad/rosco_m68k.pdf) is included for quick reading.

## Build references

1. Review the [bill of materials](../../docs/r2/BOM.md). Its source is the [KiCad CSV export](kicad/rosco_m68k.csv); confirm each footprint and package before ordering.
2. Read [jumper and power notes](../../docs/r2/JUMPERS.md) before applying power or connecting an SD card.
3. Use the [J3 expansion pinout](../../docs/r2/EXPANSION.md) when making an expansion board. **J3** is the expansion connector; **JP3** is the Flash write-enable jumper.
4. Check the KiCad PCB against [CAM outputs](CAMOutputs/) before fabrication. Regenerate Gerbers and drill files after any design change.

The KiCad files identify this board as **2.13-DEV**, dated 10 December 2023. The upstream Git branch name release/version-2.42 refers to a software release and does not certify these fabrication outputs as a final PCB revision.

## Contents

- **kicad/**: editable schematic sheets, PCB, project, local symbols and footprints, CSV BOM export, and schematic PDF.
- **CAMOutputs/**: Gerber layers and drill files.
- **docs/r2/**: [BOM, jumper notes, and expansion pinout](../../docs/README.md).

The hardware design is licensed under [CERN OHL v1.2](../../LICENCE.hardware.txt). The documentation is attributed in the [repository README](../../README.md).
