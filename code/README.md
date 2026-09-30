# SolderDemon m68k firmware and software

This directory contains firmware and software programs for SolderDemon m68k. The
source retains the `rosco_m68k` firmware ABI and upstream build identifiers.

For new programs, start with the [rosco CLI and Docker guide](../docs/development.md). See the README.md files in the subdirectories for details.

| File/directory      | Description                                    |
|:-------------------:|------------------------------------------------|
| Toolchain.md        | Host toolchain instructions for builds without Docker |
| shared              | Shared code for both firmware and software     |
| firmware            | Firmware for the board (ROM code)              |
| software            | Software (system code & libraries, examples)   |
| pld                 | [PLD sources and programming](pld/README.md)    |
| starter_projects    | Older starter examples; use rosco CLI init for new projects |
