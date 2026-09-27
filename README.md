# rosco_m68k through-hole hardware

![Populated rosco_m68k Classic v2 mainboard](images/mainboard-2.1.jpg)

A Motorola 68k single-board computer with a focus on **through-hole (THT) hardware**. This fork brings together the board design, firmware, software, and PLD code. The hardware files currently live in the original design/r2 directory; the [upstream project](https://github.com/rosco-m68k/rosco_m68k) retains the full history of other board designs.

## Find your way around

| What you need | Where to go |
| --- | --- |
| THT board design, schematic PDF, Gerbers, and drill files | [design/r2](design/r2/README.md) |
| BOM, jumper settings, and expansion pinout | [docs/r2](docs/README.md) |
| Firmware and ROM code | [code/firmware](code/firmware/) |
| PLD source and programming | [PLD guide](code/pld/README.md) |
| Software, libraries, and examples | [code/software](code/software/) |
| Recommended software workflow | [rosco CLI and Docker guide](docs/development.md) |

The R2 KiCad files are marked **2.13-DEV** (10 December 2023). This fork began from the upstream release/version-2.42 Git branch; that software version is separate from the PCB revision. Verify the schematic, PCB, and fabrication outputs together before ordering boards.

## Develop software

For new programs, use [rosco CLI](https://github.com/solderdemon/rosco-cli) with its Docker build workflow. It creates the current starter project, builds with the [SolderDemon toolchain image](https://hub.docker.com/r/solderdemon/rosco_m68k), and can upload and monitor over UART. Follow the [quick start](docs/development.md).

## At the bench

- Start with the [hardware build guide](design/r2/README.md) and [bill of materials](docs/r2/BOM.md).
- Check [power and jumper settings](docs/r2/JUMPERS.md) before applying power, particularly JP1/JP2 for FTDI power and JP3 for Flash writes.
- Use the [J3 expansion header pinout](docs/r2/EXPANSION.md) for peripherals. J3 is the header; JP3 is a different, two-pin jumper.
- For code builds, see the [firmware and software overview](code/README.md). The [older SD card guide](docs/legacy-sd-card.md) covers earlier board revisions and is kept for code users.

<details>
<summary>Photos from the project's early prototypes</summary>

These images show early project prototypes, not the populated Classic v2 board shown above.

![Early populated prototype](images/first-populated-prototype.jpg)
![Early prototype PCBs](images/4077381582746008339.jpg)

</details>

## Licences and attribution

Hardware design: [CERN Open Hardware Licence v1.2](LICENCE.hardware.txt). Software: [MIT and bundled third-party licences](LICENSE). Documentation: [Creative Commons Attribution 4.0](LICENSE.docs). Original rosco_m68k design and documentation: Ross Bamford, The Really Old-School Company Limited, and contributors. See [upstream](https://github.com/rosco-m68k/rosco_m68k) for complete history and documentation.
