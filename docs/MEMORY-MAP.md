# Memory map

This is the physical 24-bit address map of the through-hole mainboard after startup. The [address decoder PLD](../code/pld/address_decoder/ic2_address_decoder.pld) defines the board-level regions; the [firmware linker script](../code/firmware/rosco_m68k_firmware/rosco_m68k_firmware_1M.ld) and [program linker script](../code/software/libs/src/start_serial/link_scripts/hugerom_rosco_m68k_program.ld) use the same boundaries.

| Address range | Size | Use |
| --- | ---: | --- |
| `0x000000`–`0x0FFFFF` | 1 MiB | Onboard RAM |
| `0x100000`–`0xDFFFFF` | 13 MiB | Expansion address space; memory or devices depend on the attached hardware |
| `0xE00000`–`0xEFFFFF` | 1 MiB | Onboard ROM / Flash |
| `0xF00000`–`0xFFFFFF` | 1 MiB | I/O address space |

At reset, the address decoder temporarily selects ROM at low addresses so the CPU can fetch its initial vectors. After the startup cycles, RAM occupies `0x000000`–`0x0FFFFF`. The ROM image and firmware revision word are linked at `0xE00000` and `0xE00400` respectively. The DUART is addressed at odd byte addresses starting at `0xF00001`; see the [firmware register definitions](../code/firmware/rosco_m68k_firmware/include/machine.h). The I/O region is a decode window, not a promise that every address in it has a device.

## Low RAM used by firmware

The firmware reserves the first `0x2000` bytes for vectors and system data. The ranges below come from the [firmware interface reference](../code/firmware/rosco_m68k_firmware/InterfaceReference.md#2-system-data-area-memory-map).

| Address range | Use |
| --- | --- |
| `0x000000`–`0x0003FF` | Exception vectors |
| `0x000400`–`0x00041F` | System Data Block (SDB), including RAM size and UART base |
| `0x000420`–`0x0004FF` | Firmware function pointer table |
| `0x000500`–`0x00117F` | Video I/O data area |
| `0x001180`–`0x0017FF` | Firmware internal reserved area |
| `0x001800`–`0x001FFF` | Firmware BSS |

The standard program linker script begins its run area at `0x002000`. It also uses `0x040000` as a load address, so use the linker script for a program's actual layout instead of treating all higher RAM as free. For individual SDB fields and firmware calls, use the [full interface reference](../code/firmware/rosco_m68k_firmware/InterfaceReference.md).
