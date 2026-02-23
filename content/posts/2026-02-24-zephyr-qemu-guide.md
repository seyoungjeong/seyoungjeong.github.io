---
title: "Zephyr Environment Setup & QEMU Walkthrough"
date: 2026-02-24T07:40:00+09:00
description: "Mac(Apple Silicon) 환경에서 Zephyr RTOS 개발 환경 설정 및 QEMU 에뮬레이터를 통한 애플리케이션 빌드/테스트 방법"
categories: ["Zephyr"]
tags: ["Zephyr", "QEMU", "Embedded", "Mac", "Apple Silicon"]
draft: false
---

이번 포스트에서는 Mac(Apple Silicon, M1/M2/M3/M4) 환경에서 Zephyr RTOS 개발 환경을 설정하고, 실제 보드 하드웨어 없이 QEMU 에뮬레이터를 통해 애플리케이션을 빌드하고 테스트하는 방법을 알아보겠습니다.

## 0. 사전 작업 (Changes Made)

원활한 실습을 위해 이 가이드 작성 전에 다음과 같은 환경 구성을 미리 완료했습니다.

* **System Dependencies**: Installed `cmake`, `ninja`, `qemu`, `ccache` and other required homebrew packages.
* **Python Environment**: Created a virtual environment (`~/ws/zephyr-venv`), upgraded pip, and installed `west`.
* **Zephyr Workspace**: Initialized the `west` workspace and pulled all external dependencies (`west update`). Installed required Python scripts.
* **Zephyr SDK**: Downloaded and installed the `zephyr-sdk-0.16.8` with the `x86_64-zephyr-elf` toolchain for macOS ARM64.

## 1. Zephyr 가상 환경 활성화

Zephyr의 자체 빌드 시스템인 `west`와 각종 도구들을 정상적으로 사용하려면, 먼저 파이썬 가상 환경을 활성화해야 합니다. 이전에 생성해 둔 가상 환경(`~/ws/zephyr-venv`)을 로드하고 작업 디렉토리로 이동합니다.

```bash
# 가상 환경 활성화 (명령어 실행 후 터미널 프롬프트 앞에 (zephyr-venv) 표시 확인)
source ~/ws/zephyr-venv/bin/activate

# Zephyr 프로젝트 최상위 폴더로 이동
cd ~/ws/zephyr
```

아직 Zephyr SDK를 제대로 설정하지 않았다면 포팅할 대상 아키텍처(ARM, x86 등)에 맞는 툴체인과 QEMU 호스트 툴을 추가로 설치해 주어야 합니다.
```bash
# SDK 폴더로 이동 후 필수 패키지 설치
cd ~/ws/zephyr-sdk-0.16.8
./setup.sh -c -t arm-zephyr-eabi
```

## 2. QEMU를 사용한 빌드 및 실행

Zephyr는 `west build` 명령어의 플래그를 통해 빌드할 타겟 보드와 에뮬레이터 자동 실행 여부를 지정할 수 있습니다. 가장 기본 예제인 `hello_world`를 실행해 보겠습니다.

### A. 빌드 후 바로 QEMU에서 실행하기

`-t run` 옵션을 추가하면 빌드가 성공적으로 완료된 직후 자동으로 QEMU 환경을 띄워 결과를 보여줍니다. 

**ARM Cortex-M3 보드 타겟 지정 시:**
```bash
west build -p -b qemu_cortex_m3 samples/hello_world -t run
```

> **💡 팁: `-p` (pristine) 옵션이란?**
> 빌드 명령어 중간에 들어간 `-p` 옵션은 기존 빌드 디렉토리를 완전히 깨끗하게 비운 뒤(pristine) 새로 빌드하라는 뜻입니다. 
> 만약 이전에 `qemu_x86` 등 다른 보드로 빌드했던 내역이 남아있을 때 타겟을 바꾸어 바로 빌드하면 충돌 에러(`ERROR: Build directory ... targets board qemu_x86, but board qemu_cortex_m3 was specified.`)가 발생합니다. 타겟 보드를 변경할 때는 반드시 `-p` 옵션을 넣어 기존 빌드 캐시를 지워주세요!

정상적으로 빌드되었다면 텍스트 기반의 QEMU 터미널이 열리며 아래와 같이 부팅 및 문자열 출력이 이루어집니다.
```text
*** Booting Zephyr OS build 28793caf8272 ***
Hello World! qemu_cortex_m3/ti_lm3s6965
```

### B. 빌드와 실행 분리하기

빌드만 먼저 진행하고, 나중에 에뮬레이터를 구동할 수도 있습니다.
```bash
# 1. 대상 보드 빌드하기
west build -p -b qemu_cortex_m3 samples/hello_world

# 2. QEMU 환경에서 실행하기
west build -t run
```

## 3. QEMU 환경 빠져나오기

프로그램 구동을 확인한 뒤 열려있는 QEMU 터미널에서 빠져나오려면(종료하려면) 다음 단축키를 차례대로 누릅니다.
1. `Ctrl` + `A`
2. `X` (소문자 x 누름)

## 4. Apple Silicon (M 시리즈) 환경의 특징

Apple Silicon(M1, M2, M3, **M4**) 칩이 탑재된 Mac 통에서 QEMU 기반의 에뮬레이션을 사용할 때 알아두면 좋은 장점들이 있습니다.

* **네이티브 QEMU 성능**: macOS(Apple Silicon)용 SDK(aarch64)를 설치하셨다면 로제타(Rosetta) 번역 계층을 거치지 않고 네이티브 환경에서 즉시 동작하여 속도 저하가 없습니다.
* **ARM 아키텍처 에뮬레이션 친화성**: x86 보드를 테스트할 때는 아키텍처가 달라 소프트웨어적 명령어 번역 과정(TCG)이 들어가야 합니다만, **`qemu_cortex_m3` 같은 ARM 기반 보드를 가상으로 돌릴 때는 호스트(Mac)와 에뮬레이터 타겟의 기반 계열이 똑같기 때문에, 에뮬레이터 오버헤드가 매우 적어 상당히 가볍고 빠르게 동작**합니다.

따라서 M 시리즈 Mac에서는 `qemu_cortex_m3` 등 ARM 계열 가상 보드를 기준으로 삼고 테스트하는 것을 적극 추천합니다.
