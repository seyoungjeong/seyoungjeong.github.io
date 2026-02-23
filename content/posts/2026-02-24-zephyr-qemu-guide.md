---
title: "Zephyr Environment Setup & QEMU Walkthrough"
date: 2026-02-24T07:40:00+09:00
description: "Setting up Zephyr RTOS development environment on Mac (Apple Silicon) and building/testing applications via QEMU emulator"
categories: ["Zephyr"]
tags: ["Zephyr", "QEMU", "Embedded", "Mac", "Apple Silicon"]
draft: false
---

In this post, we will explore how to set up the Zephyr RTOS development environment on a Mac (Apple Silicon, M1/M2/M3/M4), and how to build and test applications using the QEMU emulator without actual board hardware.

## 0. Preliminary Work (Changes Made)

For a smooth walkthrough, the following environment configuration has been completed prior to writing this guide.

* **System Dependencies**: Installed `cmake`, `ninja`, `qemu`, `ccache` and other required homebrew packages.
* **Python Environment**: Created a virtual environment (`~/ws/zephyr-venv`), upgraded pip, and installed `west`.
* **Zephyr Workspace**: Initialized the `west` workspace and pulled all external dependencies (`west update`). Installed required Python scripts.
* **Zephyr SDK**: Downloaded and installed the `zephyr-sdk-0.16.8` with the `x86_64-zephyr-elf` toolchain for macOS ARM64.

## 1. Activating Zephyr Virtual Environment

To use Zephyr's build system, `west`, and various tools properly, you first need to activate the Python virtual environment. Load the previously created virtual environment (`~/ws/zephyr-venv`) and navigate to the working directory.

```bash
# Activate virtual environment (verify the (zephyr-venv) prefix in the prompt)
source ~/ws/zephyr-venv/bin/activate

# Navigate to the Zephyr project root folder
cd ~/ws/zephyr
```

If you haven't properly set up the Zephyr SDK yet, you need to install the toolchain suitable for the target architecture (ARM, x86, etc.) you want to port to, along with the QEMU host tools.
```bash
# Navigate to the SDK folder and install required packages
cd ~/ws/zephyr-sdk-0.16.8
./setup.sh -c -t arm-zephyr-eabi
```

## 2. Building and Running with QEMU

Zephyr allows you to easily specify the target board and whether to automatically run the emulator through the flags of the `west build` command. Let's try running the most basic example, `hello_world`.

### A. Run in QEMU Immediately After Build

Adding the `-t run` option will automatically launch the QEMU environment and show the results immediately after a successful build.

**When targeting the ARM Cortex-M3 board:**
```bash
west build -p -b qemu_cortex_m3 samples/hello_world -t run
```

> **💡 Tip: What is the `-p` (pristine) option?**
> The `-p` option included in the build command tells the system to completely clear (pristine) the existing build directory and perform a fresh build.
> If you previously built for another board like `qemu_x86` and try to build again by just changing the target, a conflict error (`ERROR: Build directory ... targets board qemu_x86, but board qemu_cortex_m3 was specified.`) will occur. When changing the target board, be sure to include the `-p` option to clear the existing build cache!

If the build is successful, a text-based QEMU terminal will open, showing the booting process and string output like below:
```text
*** Booting Zephyr OS build 28793caf8272 ***
Hello World! qemu_cortex_m3/ti_lm3s6965
```

### B. Separating Build and Execution

You can also proceed with just the build first, and run the emulator later.
```bash
# 1. Build the target board
west build -p -b qemu_cortex_m3 samples/hello_world

# 2. Run in QEMU environment
west build -t run
```

## 3. Exiting the QEMU Environment

After verifying the program execution, you can exit the open QEMU terminal by pressing the following shortcuts in sequence:
1. `Ctrl` + `A`
2. `X` (press lowercase x)

## 4. Characteristics of Apple Silicon (M Series) Environment

There are some advantages to know when using QEMU-based emulation on Macs equipped with Apple Silicon (M1, M2, M3, **M4**) chips.

* **Native QEMU Performance**: If you have installed the SDK for macOS (Apple Silicon) (`aarch64`), it operates immediately in the native environment without going through the Rosetta translation layer, avoiding any speed degradation.
* **ARM Architecture Emulation Affinity**: When testing x86 boards, the architectural difference requires a software instruction translation process (TCG). However, **when running an ARM-based board like `qemu_cortex_m3` virtually, the host (Mac) and emulator target share the same base architecture, meaning the emulator overhead is extremely low, allowing it to run significantly lighter and faster.**

Therefore, on M-series Macs, it is highly recommended to use ARM-family virtual boards like `qemu_cortex_m3` as the standard for testing.
