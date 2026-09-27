# R2 jumpers, power, and SD card

These notes are adapted from the original *Classic v2 Additional Information* sheet for the R2 mainboard. Confirm jumper positions against the [schematic](../../design/r2/kicad/rosco_m68k.pdf) and board silkscreen before applying power.

| Jumper | Closed | Normal use |
| --- | --- | --- |
| JP1 / JP2 | Allows power from the corresponding FTDI serial module | Leave both open when using the board's external power input. Close **only one** when deliberately powering through an FTDI module. |
| JP3 | Enables hardware writing to the Flash ROMs | Leave open unless running a Flash update. |
| JP4 | Changes expansion RAM behaviour for the original rosco_m68k memory expansion board | Leave open for other configurations. |

## Power through FTDI

Never close JP1 and JP2 together. Do not connect external power while either FTDI power jumper is closed. The original R2 notice states the mainboard alone requires **at least 500 mA**; check that the host and FTDI module can supply the complete build.

## SD card header

The SPI SD card header uses **5 V** signals. Use an Arduino-compatible SD card adapter with built-in **5 V to 3.3 V level conversion**. Do not connect a bare 3.3 V SD card directly.

## Expansion power

The J3 expansion connector exposes 5 V and ground. The original [J3 pinout](EXPANSION.md) recommends drawing no more than **500 mA** from its 5 V pin, with **1 A** stated as an absolute maximum. Account for the complete board's power supply and use a shared ground if powering a peripheral separately.
