# Through-hole mainboard design

![Populated Classic v2 board](../images/mainboard-2.1.jpg)

This directory contains the through-hole mainboard design. Open the [KiCad project](kicad/rosco_m68k.kicad_pro) to inspect or edit the board. The schematics are split into CPU, memory, GALs, DUART, reset, and expansion sheets. A [schematic PDF](kicad/rosco_m68k.pdf) is included for quick reading.

## Build references

1. Review the [bill of materials](../docs/BOM.md). Its source is the [KiCad CSV export](kicad/rosco_m68k.csv); confirm each footprint and package before ordering.
2. Read [jumper and power notes](../docs/JUMPERS.md) before applying power or connecting an SD card.
3. Use the [J3 expansion pinout](../docs/EXPANSION.md) when making an expansion board. **J3** is the expansion connector; **JP3** is the Flash write-enable jumper.
4. Check the KiCad PCB against [CAM outputs](CAMOutputs/) before fabrication. Regenerate Gerbers and drill files after any design change.

## Contents

- **kicad/**: editable schematic sheets, PCB, project, local symbols and footprints, CSV BOM export, and schematic PDF.
- **CAMOutputs/**: Gerber layers and drill files.
- **docs/**: [BOM, jumper notes, and expansion pinout](../docs/README.md).

The hardware design is licensed under [CERN OHL v1.2](../LICENCE.hardware.txt). The documentation is attributed in the [repository README](../README.md).
