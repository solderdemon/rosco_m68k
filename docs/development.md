# Develop software with rosco CLI

[rosco CLI](https://github.com/solderdemon/rosco-cli) is the recommended way to create, build, upload, and monitor rosco_m68k programs. It keeps the build and serial workflow in one command-line tool.

## Start a new project

Install rosco CLI using the instructions in its [README](https://github.com/solderdemon/rosco-cli#install-from-this-checkout), then create a new C project:

```sh
rosco init hello --board rosco_m68k --language c --docker --target hardware --yes
cd hello
rosco doctor
rosco build
```

Use `--language asm` for an assembly project. The CLI creates the current starter files itself, so there is no need to copy this repository's older `code/starter_projects` directories into a new project.

The generated project records Docker as its build toolchain. Docker must be installed and running. On ARM hosts, the [CLI documentation](https://github.com/solderdemon/rosco-cli#configuration) describes setting `build.docker.platform = "linux/amd64"` if the image requires emulation.

## Run on the board

Connect the USB serial adapter and run:

```sh
rosco run
```

`rosco run` automatically selects the USB-UART port when there is one matching device. It builds, uploads through Kermit, and monitors UART output. If discovery cannot choose a port, run `rosco ports` to list USB-UART candidates (or `rosco ports --all` for other serial ports), then pass the correct port explicitly with `rosco run --port <port>`. See the [CLI README](https://github.com/solderdemon/rosco-cli#typical-workflow) for separate build, upload, and monitor commands.

## Emulate the board

The separate [SolderDemon rosco-emulator](https://github.com/solderdemon/rosco-emulator) supports both rosco_m68k and rosco_6502. rosco CLI can create a project that runs in the emulator through Docker:

```sh
rosco init hello --board rosco_m68k --language c --docker --target emulator --emulator-docker --yes
cd hello
rosco run
```

For a rosco_6502 project, choose `--board rosco_6502`. The emulator also has its own [Docker image and usage instructions](https://github.com/solderdemon/rosco-emulator#docker).

## Existing projects and host builds

From an existing compatible software project, `rosco build --docker` selects the Docker toolchain for that run. The older [host toolchain instructions](../code/Toolchain.md) remain available if you deliberately build without Docker. The older [starter projects](../code/starter_projects/README.md) are retained as examples; use `rosco init` for a fresh project.
