# Software

This directory contains various different software programs for the 
rosco_m68k.

> For a new program, use [rosco CLI](https://github.com/solderdemon/rosco-cli) to create a starter project and build it with Docker. See the [development quick start](../../docs/development.md). The older `code/starter_projects` examples remain available.

Specifically:

| Filename            | Description                                    |
|:-------------------:|------------------------------------------------|
| 2dmaze              | A 2d maze demo of libm (thanks to mattuna15)   |
| adventure           | A port of Jeff Tranter's 'Adventure' (game).   | 
| dhrystone           | Dhrystone benchmark (thanks to Xark)           |
| easy68k-demo        | Demo of the easy68k firmware interface         |
| ehbasic             | Lee Davison's ehBASIC (rosco_m68k port)        |
| lcd-ili9341         | SPI demo with ILI9341 LCD (thanks to Xark)     |
| libs                | All shared functions are built as libraries.   |
| life                | Conway's Game of Life (thanks to mattuna15)    |
| memcheck            | Memory checker / basic sysinfo tool            |
| sdfat_demo          | Demo code for using firmware SD interface      |
| sdfat_menu          | **Awesome** SD Card bootload menu (thanks Xark)| 
| gpiodemo            | Stupid-simple GPIO example                     |
| vterm               | ANSI terminal emulation (thanks to mattuna15)  |
 
## Getting Started

### Toolchain for the bundled examples

For new projects, [rosco CLI with Docker](../../docs/development.md) provides the recommended toolchain. The direct Make commands below require a host GNU M68k toolchain; see the [host toolchain guide](../Toolchain.md) if you choose that route.

### Shared Libraries

The `libs` directory contains code that the other programs depend on. 
At a minimum, most (if not all) programs depend on the `start_serial`
library, which provides the entry point for programs loaded by the 
serial firmware and takes care of relocating loaded code and running
the `kmain` method.

The libraries must be built before the rest of the programs can be 
built - this is simple:

```
cd libs
make install
```

This doesn't install anything globally on your system - it just builds
all the libraries and makes them available under `libs/build`, where the
rest of the programs expect to find them.

> **Note** Any problems at this point are likely due to an incomplete or
  incorrectly built toolchain. See 
  [host toolchain guide](../Toolchain.md)
  for help building a correct toolchain with the expected versions.
  While building with GCC > 7.5.0 should work (please file a bug if you
  find it doesn't!) building with older versions is not supported.

## Building the examples

You can build all example programs in one go by simple typing `make` 
in this directory. This will build binaries for each example in their
respective directories.

Alternatively, each of the example programs contains a `Make` build - 
simply `cd` into the appropriate directory and type `make all`.

This will build a few different artefacts, chief amongst which will be
the `bin` file, which is a serial-bootloader compatible binary that 
can be uploaded to your rosco_m68k via Kermit.

There is a short `README.md` in each program directory that contains
documentation specific to that program - see those for detailes of the
program and any specific build instructions.

> **Note** if your rosco_m68k has the flash ROM adapter and is 
running a `HUGEROM` build of the firmware, you will need to build the
examples with `ROSCO_M68K_HUGEROM` set to `true`, e.g. by passing on
the command line (`ROSCO_M68K_HUGEROM=true make clean all`) or by
setting an environment variable for a more permanent solution.

## Building your own projects

Create a new C or assembly project with `rosco init` as shown in the [development quick start](../../docs/development.md). The [older starter projects](../starter_projects/README.md) are retained as examples.

