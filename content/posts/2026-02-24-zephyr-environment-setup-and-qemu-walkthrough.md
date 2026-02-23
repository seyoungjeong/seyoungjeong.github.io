---
title: "Zephyr Environment Setup & QEMU Walkthrough"
date: 2026-02-24T07:07:21+09:00
description: "Zephyr OS 환경 구축 및 QEMU 실행 가이드"
categories: ["Zephyr"]
tags: ["Zephyr", "QEMU", "Embedded"]
draft: false 
---

<!-- 여기에 글 작성을 시작하세요. -->
# Zephyr Environment Setup & QEMU Walkthrough

We have successfully configured your local environment to build and run Zephyr OS samples on QEMU.

## Changes Made
1. **System Dependencies:** Installed `cmake`, `ninja`, `qemu`, `ccache` and other required homebrew packages.
2. **Python Environment:** Created a virtual environment (`~/ws/zephyr-venv`), upgraded pip, and installed west.
3. **Zephyr Workspace:** Initialized the `west` workspace and pulled all external dependencies (`west update`). Installed required Python scripts.
4. **Zephyr SDK:** Downloaded and installed the `zephyr-sdk-0.16.8` with the `x86_64-zephyr-elf` toolchain for macOS ARM64.

## Validation Results
We successfully built the `hello_world` application for the `qemu_x86` board:
```bash
source ~/ws/zephyr-venv/bin/activate
cd ~/ws/zephyr
west build -p auto -b qemu_x86 samples/hello_world
```

And verified it running under QEMU:
```bash
west build -t run
```

### QEMU Execution Output
During the `west build -t run` step, the QEMU emulator successfully started the Zephyr kernel and executed our program, producing the expected terminal output:

```text
*** Booting Zephyr OS build 28793caf8272 ***
Hello World! qemu_x86/atom
```

The QEMU environment is now fully healthy and ready for your development workflow. You can build other samples from the `samples/` directory and run them the same way!
