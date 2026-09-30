# rosco_m68k classic THT r2.14 glue logic: two ATF1502AS

Board revision 2.14 replaces the four ATF22V10C GALs of r2.13 (IC2 address decoder, IC3 DUART
select, IC5 general glue, IC6 watchdog) with two **ATF1502AS-10JU44** CPLDs in through-hole
PLCC-44 sockets, like the DUART IC4:

| Ref | Source | Does | Replaces |
|---|---|---|---|
| IC2 | [`ic2_decoder.pld`](ic2_decoder.pld) | address decode (RAM/ROM/IO/expansion), DTACK, WR, boot latch, ANYIACK | r2.13 IC2 + the boot counter and ANYIACK of IC5 |
| IC3 | [`ic3_glue.pld`](ic3_glue.pld) | DUART /CS and /IACK, RESET/HALT, RUN LED, bus-error watchdog | r2.13 IC3 + IC6 + the rest of IC5 |

The equations are those of the r2.13 GALs, unchanged, and every board net keeps its name and
level. BOOT and ANYIACK, which ran between the GALs, are internal to IC2 now (ANYIACK is decoded
in IC3 as well, for the watchdog and DUART IACK), so no wire runs between IC2 and IC3. IC2 uses
24 pins and 16 macrocells, IC3 31 pins and 21 macrocells.

## Building

```sh
./build.sh
```

It needs a running Docker: it uses the `dinoboards/cpld-toolchain` image (WinCUPL plus the
Atmel `find1502` fitter, see `tools/cpld-toolchain` in the workspace), writes `bin/*.jed`, and
fails if the fitter moved any pin away from where the `.pld` puts it -- the board is routed to
those pins.

## Checking the logic

```sh
python design/tools/verify_cpld.py [steps] [seed]
```

runs the r2.13 GALs from their real JEDEC fuse maps (`../address_decoder`, `../duartsel`,
`../glue`, `../watchdog`) and the r2.14 CPLDs from these sources side by side on random bus
traffic and fails on the first net that differs -- all 14 driven nets, the open-drain ones
resolved as wired-AND with the CPU pulling RESET/HALT as well. The stimulus makes the boot latch
set and the watchdog fire, and the run fails if either never happens.

## Programming

The ATF1502AS is programmed in circuit over JTAG; the TL866/minipro cannot program it. Header J9
has the Altera/Atmel 10-pin layout (1 TCK, 2 GND, 3 TDO, 4 VCC, 5 TMS, 9 TDI, 10 GND) and the
two chips are chained TDI -> IC2 -> IC3 -> TDO, so IC2 is the first device in the chain. Use an
Atmel ATDH1150USB with ATMISP, or any FT232H/FT2232H adapter with OpenOCD (convert the `.jed` to
SVF first). The board must be powered while programming.

Both designs keep JTAG enabled (`JTAG = ON`) with the internal pull-ups on TDI and TMS. Do not
turn JTAG off: the chip can then only be recovered with a high-voltage programmer.

## Pinout

The `PIN` lines in the `.pld` files are the only place the pinout is written down;
`design/tools/cpld_sch.py` and `cpld_board.py` read them. They were chosen by
`cpld_board.py --suggest`, which puts each signal on the pin nearest to where its net already
runs on the board. To move a pin: edit the `.pld`, run `./build.sh`, `verify_cpld.py`, then
`cpld_sch.py`, `cpld_board.py` and `cpld_route.py` (see [design/README.md](../../../design/README.md)).
