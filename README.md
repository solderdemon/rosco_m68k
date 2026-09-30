# SolderDemon m68k

![Assembled rosco r2.42 mainboard, the GAL version SolderDemon m68k r1 grew from](images/mainboard-r2.42.jpg)

SolderDemon develops a line of Motorola 68k computers built from **through-hole (THT) parts**. This repository holds its mainboard: the board design, firmware, software and CPLD code. Expansion boards such as the [busboard](https://github.com/solderdemon/solderdemon_m68k-busboard) plug into its J3 expansion connector.

The mainboard is built on [rosco_m68k](https://github.com/rosco-m68k/rosco_m68k) by Ross Bamford, The Really Old-School Company Limited, and contributors. SolderDemon boards carry their own revision numbers, starting at r1; the rosco r2.x numbers are the history they grew from. The photo above is the assembled rosco r2.42 board, the GAL version that r1 grew from.

## The board: r1

r1 is the next release and is not made yet. KiCad renders of it, top and bottom:

<p>
  <img src="images/r1-render-top.png" alt="SolderDemon m68k r1, top side, KiCad render" width="49%">
  <img src="images/r1-render-bottom.png" alt="SolderDemon m68k r1, bottom side with the SolderDemon identity, KiCad render" width="49%">
</p>

| | |
| --- | --- |
| CPU | MC68010, 10 MHz |
| Memory | 1 MB Flash ROM (2 × SST39SF040), 1 MB SRAM (2 × AS6C4008) |
| Glue logic | 2 × ATF1502AS CPLD in PLCC-44 sockets, programmed in circuit over JTAG (J9) |
| I/O | XR68C681 DUART: two UARTs (J1, J2), SD card over SPI (J4) |
| Expansion | 64-pin J3 connector |
| PCB | 165 × 100 mm, 4 layers |

What changed from rosco r2.42 is in the [design notes](design/README.md).

## Find your way around

| What you need | Where to go |
| --- | --- |
| Board design | [design](design/README.md) |
| BOM, jumper settings, memory map, and expansion pinout | [docs](docs/README.md) |
| Firmware and ROM code | [code/firmware](code/firmware/) |
| PLD source and programming | [PLD guide](code/pld/README.md) |
| Software, libraries, and examples | [code/software](code/software/) |
| Recommended software workflow | [rosco CLI and Docker guide](docs/development.md) |
| Emulator for rosco_m68k and rosco_6502 | [SolderDemon rosco-emulator](https://github.com/solderdemon/rosco-emulator) |

## Develop software

For new programs, use [rosco CLI](https://github.com/solderdemon/rosco-cli) with its Docker build workflow. It creates the current starter project, builds through Docker, and can upload and monitor over UART. Follow the [quick start](docs/development.md).

## At the bench

- Start with the [hardware build guide](design/README.md) and [bill of materials](docs/BOM.md).
- Check [power and jumper settings](docs/JUMPERS.md) before applying power, particularly JP1/JP2 for FTDI power and JP3 for Flash writes.
- Use the [J3 expansion header pinout](docs/EXPANSION.md) for peripherals. J3 is the header; JP3 is a different, two-pin jumper.
- For code builds, see the [firmware and software overview](code/README.md). The [older SD card guide](docs/legacy-sd-card.md) covers earlier board revisions and is kept for code users.

<details>
<summary>Photos from the project's early prototypes</summary>

These images show early project prototypes, not the assembled r2.42 board shown above.

![Early populated prototype](images/first-populated-prototype.jpg)
![Early prototype PCBs](images/4077381582746008339.jpg)

</details>

## Licences and attribution

Hardware design: [CERN Open Hardware Licence v1.2](LICENCE.hardware.txt). Software: [MIT](LICENSE) with [third-party notices](licenses/README.md). Documentation: [Creative Commons Attribution 4.0](licenses/LICENSE.docs). Original rosco_m68k design and documentation: Ross Bamford, The Really Old-School Company Limited, and contributors. See [upstream](https://github.com/rosco-m68k/rosco_m68k) for complete history and documentation.

**SolderDemon modification notice (2026-09-30):** SolderDemon m68k adapts the original rosco_m68k project, including a reworked through-hole mainboard (CPLDs instead of GALs, r1 layout and identity), the CPLD logic, and the build documentation. The original authorship and licence notices remain with the source files.
