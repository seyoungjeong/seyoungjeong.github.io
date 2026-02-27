---
title: "Zephyr RTOS: README 누락 샘플 문서화 기여"
date: 2026-02-24T12:50:00+09:00
description: "Zephyr 프로젝트에서 README가 누락된 5개 샘플에 대한 문서를 작성하고 PR을 제출한 기록입니다."
categories: ["Zephyr", "Tech"]
tags: ["Zephyr", "Open Source", "Documentation", "Contributing"]
draft: false
---

## 문제 요약

Zephyr RTOS의 `samples/` 디렉토리 내 다수의 샘플이 README 문서 없이 배포되고 있는 문제. 사용자가 샘플의 목적, 요구사항, 빌드 방법을 파악하기 어려움.

- **원본 이슈**: [zephyrproject-rtos/zephyr#27805](https://github.com/zephyrproject-rtos/zephyr/issues/27805)

## 작업 내용

5개 샘플에 대해 소스 코드(`main.c`), 설정(`prj.conf`, `sample.yaml`), 보드 overlay를 분석하여 Zephyr 표준 포맷(`:orphan:`, `zephyr-app-commands` directive)에 맞춘 `README.rst`를 작성함.

| 샘플 | 내용 |
|------|------|
| `espressif/ethernet` | ESP32 Ethernet Kit DHCP/DNS/NET_SHELL |
| `mec172xevb/qmspi_ldma` | QMSPI SPI 플래시 읽기/쓰기/검증 (Dual/Quad) |
| `mec172xevb/rom_api` | ROM API 기반 SHA-224/256/384/512 해시 검증 |
| `nordic/nrf_sys_event` | nRF 상수 지연 모드 및 RRAMC 웨이크업 |
| `ipm_mcux/remote` | NXP LPC 메일박스 IPM 리모트 코어 에코 |

## 활동 로그

- **2026-02-24**: 5개 샘플 README.rst 작성 및 [PR #104439](https://github.com/zephyrproject-rtos/zephyr/pull/104439) 제출.
- **2026-02-24**: 메인테이너 [@kartben](https://github.com/kartben) 리뷰 피드백 수신:
  - 표준 템플릿(`doc/templates/sample.tmpl`) 미준수 → 형식 재작성 필요.
  - 5개 샘플을 개별 PR로 분리 제출할 것 (각 플랫폼 메인테이너 리뷰 필요).
  - 보드 문서 링크 추가 필요.
- **2026-02-25**: 피드백 반영하여 `samples/subsys/pm/device_pm` README.rst를 표준 템플릿 기반으로 재작성, `qemu_x86`에서 빌드/실행 검증 후 [PR #104503](https://github.com/zephyrproject-rtos/zephyr/pull/104503) 제출.
  - 빌드 시 발생하는 Sphinx 경고(Doxygen group name 등) 수정 커밋 추가.
- **2026-02-26**: 리뷰어 [@JordanYates](https://github.com/JordanYates) 리뷰 피드백 반영:
  - 샘플 코드 내의 잘못된 API 사용(`pm_device_runtime_enable` 대신 `pm_device_driver_init` 사용)을 수정하여 불필요한 초기 suspend 로그 출력 제거.
  - 수정된 샘플 코드 동작 결과를 반영하여 README.rst의 Expected Output 항목 업데이트.
- **2026-02-27**: 추가 리뷰 피드백 반영 및 CI 실패 수정:
  - `prj.conf`에 `CONFIG_PM_DEVICE_RUNTIME_DEFAULT_ENABLE=y` 추가 — 이 설정 없이는 런타임 PM이 실제로 활성화되지 않는 문제 해결.
  - CI twister 테스트 실패 원인 분석: `sample.yaml` harness regex가 이전 출력 패턴(pre-main suspending 메시지)을 기대하여 120초 타임아웃 발생.
  - `sample.yaml` harness regex 패턴을 새 출력에 맞게 수정하여 CI 테스트 통과 가능하도록 반영.
