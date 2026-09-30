# SolderDemon m68k retro computer

![Populated rosco_m68k Classic v2 mainboard](images/mainboard-2.1.jpg)

SolderDemon m68k is a Motorola 68k single-board computer with a focus on **through-hole (THT) hardware**. It is derived from [rosco_m68k](https://github.com/rosco-m68k/rosco_m68k), created by Ross Bamford, The Really Old-School Company Limited, and contributors. This fork brings together the board design, firmware, software, and PLD code. The hardware design lives in design/; the upstream project retains the full history of other board designs.

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

These images show early project prototypes, not the populated Classic v2 board shown above.

![Early populated prototype](images/first-populated-prototype.jpg)
![Early prototype PCBs](images/4077381582746008339.jpg)

</details>

## Licences and attribution

Hardware design: [CERN Open Hardware Licence v1.2](LICENCE.hardware.txt). Software: [MIT](LICENSE) with [third-party notices](licenses/README.md). Documentation: [Creative Commons Attribution 4.0](licenses/LICENSE.docs). Original rosco_m68k design and documentation: Ross Bamford, The Really Old-School Company Limited, and contributors. See [upstream](https://github.com/rosco-m68k/rosco_m68k) for complete history and documentation.

**SolderDemon modification notice (2026-09-28):** This fork adapts the original rosco_m68k project, including revisions to the through-hole mainboard design, PLD logic, and accompanying build documentation. The original authorship and licence notices remain with the source files.
