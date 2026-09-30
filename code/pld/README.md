# PLD firmware

From board revision 2.14 the through-hole mainboard uses two **ATF1502AS-10JU44** CPLDs in PLCC-44
sockets. Their sources, build script and programming notes are in [cpld/](cpld/README.md):

| Board reference | Function | Source | Programming image |
| --- | --- | --- | --- |
| IC2 | Address decoder, DTACK, boot latch | [cpld/ic2_decoder.pld](cpld/ic2_decoder.pld) | `cpld/bin/ic2_decoder.jed` |
| IC3 | DUART select, reset glue, watchdog | [cpld/ic3_glue.pld](cpld/ic3_glue.pld) | `cpld/bin/ic3_glue.jed` |

The CPLDs are programmed in circuit over JTAG (header J9); a TL866/Minipro cannot program them.

## r2.13 and earlier: four ATF22V10C

Boards up to r2.13 use four **ATF22V10C** GALs. Their sources and images stay here, both for those
boards and as the reference `design/tools/verify_cpld.py` checks the CPLDs against:

| Board reference | Function | Source | Programming image |
| --- | --- | --- | --- |
| IC2 | Address decoder | [address_decoder/ic2_address_decoder.pld](address_decoder/ic2_address_decoder.pld) | [ic2_address_decoder.jed](address_decoder/ic2_address_decoder.jed) |
| IC3 | DUART select | [duartsel/ic3_duart_sel.pld](duartsel/ic3_duart_sel.pld) | [ic3_duart_sel.jed](duartsel/ic3_duart_sel.jed) |
| IC5 | Glue logic | [glue/ic5_glue_logic.pld](glue/ic5_glue_logic.pld) | [ic5_glue_logic.jed](glue/ic5_glue_logic.jed) |
| IC6 | Watchdog | [watchdog/ic6_watchdog.pld](watchdog/ic6_watchdog.pld) | [ic6_watchdog.jed](watchdog/ic6_watchdog.jed) |

The .pld files are GALasm sources. The .jed files are the images used by the burn scripts; .chp, .fus, and .pin are accompanying output reports. **A burn script writes its existing .jed file; it does not compile the .pld source.** Regenerate and check the programming image after changing source logic.

Each directory has a burn.sh script that invokes Minipro for an ATF22V10C(UES). Use a compatible programmer, confirm the target IC reference, and run the script **from its own directory** because the image path is relative. For example:

```sh
cd code/pld/address_decoder
bash burn.sh
```

Repeat from the corresponding directory for IC3, IC5, and IC6. The [toolchain notes](../Toolchain.md) include Minipro setup.
