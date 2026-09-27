# PLD firmware

The through-hole mainboard uses four **ATF22V10C** programmable logic devices. Their sources and programming images are organised by function:

| Board reference | Function | Source | Programming image |
| --- | --- | --- | --- |
| IC2 | Address decoder | [address_decoder/ic2_address_decoder.pld](address_decoder/ic2_address_decoder.pld) | [ic2_address_decoder.jed](address_decoder/ic2_address_decoder.jed) |
| IC3 | DUART select | [duartsel/ic3_duart_sel.pld](duartsel/ic3_duart_sel.pld) | [ic3_duart_sel.jed](duartsel/ic3_duart_sel.jed) |
| IC5 | Glue logic | [glue/ic5_glue_logic.pld](glue/ic5_glue_logic.pld) | [ic5_glue_logic.jed](glue/ic5_glue_logic.jed) |
| IC6 | Watchdog | [watchdog/ic6_watchdog.pld](watchdog/ic6_watchdog.pld) | [ic6_watchdog.jed](watchdog/ic6_watchdog.jed) |

The .pld files are GALasm sources. The .jed files are the images used by the burn scripts; .chp, .fus, and .pin are accompanying output reports. **A burn script writes its existing .jed file; it does not compile the .pld source.** Regenerate and check the programming image after changing source logic.

## Programming

Each directory has a burn.sh script that invokes Minipro for an ATF22V10C(UES). Use a compatible programmer, confirm the target IC reference, and run the script **from its own directory** because the image path is relative. For example:

```sh
cd code/pld/address_decoder
bash burn.sh
```

Repeat from the corresponding directory for IC3, IC5, and IC6. The [toolchain notes](../Toolchain.md) include Minipro setup. The [hardware BOM](../../docs/r2/BOM.md) lists the four PLDs.
