# R2 bill of materials

This table is transcribed from the KiCad CSV export at [kicad/rosco_m68k.csv](../../design/r2/kicad/rosco_m68k.csv). It has **31 part lines and 84 component placements**. It is a design BOM, not a verified purchasing list; check the schematic, PCB footprints, and desired assembly options before ordering.

| Qty | References | Value / part | KiCad footprint |
| ---: | --- | --- | --- |
| 1 | S1 | 10-XX | B3F-10XX |
| 2 | R19,R11 | 10K | 0207_10 |
| 2 | C1,C2 | 7pF | C2.5_or_3.5-3 |
| 22 | C7,C8,C9,C20,C23,C24,C22,C26,C13,C27,C28,C30,C31,C6,C25,C29,C12,C10,C5,C4,C3,C32 | 100nF | C2.5-3 |
| 7 | C16,C17,C18,C19,C14,C15,C11 | 100uF | E2,5-5 |
| 1 | C21 | 470uF | E3,5-10 |
| 1 | IC4 | XR68C681CJTR-F | PLCC-44_THT-Socket |
| 4 | IC5,IC6,IC3,IC2 | ATF22V10C | DIP-24_W7.62mm_Socket_LongPads |
| 4 | JP1,JP2,JP3,JP4 | Jumper | 1X02 |
| 2 | LED3,LED1 | GREEN | LED5MM |
| 2 | LED4,LED2 | RED | LED5MM |
| 1 | Q1 | 3.6864MHz | Crystal_HC49-4H_Vertical |
| 1 | Q2 | 5H8ET-10.000 | Oscillator_DIP-8 |
| 2 | U4,U3 | AS6C4008-55PCN | DIP-32_W15.24mm_LongPads |
| 2 | U2,U1 | SST39SF040 | DIP-32_W15.24mm_LongPads |
| 1 | J3 | Conn_02x32_Odd_Even | PinHeader_2x32_P2.54mm_Vertical |
| 12 | R8,R7,R9,R10,R32,R31,R12,R15,R17,R18,R3,R16 | 4K7 | 0207_10 |
| 1 | J4 | Conn_01x06 | 1X06 |
| 1 | J2 | UART_B | 1X06 |
| 1 | J1 | UART_A | 1X06 |
| 1 | J5 | PWR | 1X02 |
| 1 | IC15 | 555N | DIP-8_W7.62mm_LongPads |
| 1 | R27 | 2K2 | 0207_10 |
| 1 | R28 | 270R | 0207_10 |
| 4 | R13,R14,R1,R2 | 330R | 0207_10 |
| 1 | R21 | 1K2 | 0207_10 |
| 1 | J6 | Conn_01x05_Male | PinHeader_1x05_P2.54mm_Vertical |
| 1 | J7 | Conn_01x01_Male | PinHeader_1x01_P2.54mm_Vertical |
| 1 | IC7 | 74LS148 | DIP-16_W7.62mm_LongPads |
| 1 | J8 | Conn_01x02_Male | PinHeader_1x02_P2.54mm_Vertical |
| 1 | IC1 | MC68010P10 | DIL64 |

## Items outside the component count

- The CSV also contains **four M3 mounting holes** and **six logo or compliance artwork objects**. They are PCB features, not parts to buy.
- The bare PCB and any required programming of the ATF22V10C GALs and Flash ROMs are not included as BOM lines. See the [PLD programming guide](../../code/pld/README.md) for IC2, IC3, IC5, and IC6.
- The original R2 packing list separately mentioned sockets for IC1 (DIL64, 1), IC2/IC3/IC5/IC6 (DIL24, 4), IC4 (PLCC44, 1), IC7 (DIL16, 1), IC15 (DIL08, 1), and U1/U2/U3/U4 (DIL32, 4). Treat these as assembly choices and verify fit against the PCB.
- The older packing list differs from this KiCad CSV for some headers (including J6 and J8). This table follows the CSV; inspect the current PCB before ordering those headers.

The source CSV has no supplier or manufacturer part numbers. Package names in this table are KiCad footprint identifiers, not vendor order codes.
