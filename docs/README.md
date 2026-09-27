# Documentation

## Through-hole board

- [Parts and quantities](BOM.md): bill of materials from the KiCad CSV export.
- [Jumpers, power, and SD card](JUMPERS.md): JP1 through JP4 and the 5 V SD interface.
- [J3 expansion pinout](EXPANSION.md): 64-pin header signals and electrical notes.
- [Memory map](MEMORY-MAP.md): RAM, expansion, ROM, I/O, and firmware-reserved RAM.
- [Hardware design guide](../design/README.md): KiCad source, schematic PDF, and CAM files.

## Code

- [Recommended rosco CLI and Docker workflow](development.md)
- [Emulator workflow](development.md#emulate-the-board) for rosco_m68k and rosco_6502

- [Firmware and software overview](../code/README.md)
- [Firmware interface reference](../code/firmware/rosco_m68k_firmware/InterfaceReference.md)
- [Toolchain setup](../code/Toolchain.md)
- [PLD source and programming](../code/pld/README.md)
- [Legacy SD card guide](legacy-sd-card.md), written for older board revisions

These board notes are adapted from the original project documents. See the [repository README](../README.md) for attribution and licences.
