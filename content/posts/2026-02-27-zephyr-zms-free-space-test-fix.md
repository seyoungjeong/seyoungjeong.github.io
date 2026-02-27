---
title: "Zephyr RTOS: ZMS free space 테스트 assertion 실패 수정"
date: 2026-02-27T13:40:00+09:00
description: "ZMS test_zms_free_space 테스트가 write_block_size에 따른 ATE 정렬 패딩을 고려하지 않아 발생하는 assertion 실패를 수정한 기록입니다."
categories: ["Zephyr", "Tech"]
tags: ["Zephyr", "Open Source", "Bug Fix", "Contributing"]
draft: false
---

## 문제 요약

ZMS(Zephyr Memory Storage)의 `test_zms_free_space` 테스트가 `write_block_size > 1`인 환경(섹터 크기 4KB 이상)에서 assertion 실패. 테스트가 `sizeof(struct zms_ate)`를 하드코딩하여 free space를 계산하지만, ZMS 내부는 `write_block_size`의 배수로 올림한 `ate_size`를 사용하기 때문에 값이 불일치.

- **원본 이슈**: [zephyrproject-rtos/zephyr#101880](https://github.com/zephyrproject-rtos/zephyr/issues/101880)

## 원인 분석

`zms_mount()` 시 ATE 크기는 `zms_al_size(fs, sizeof(struct zms_ate))`로 결정되어 `write_block_size`의 배수로 올림됨. 테스트 코드는 이를 무시하고 컴파일 타임 `sizeof(struct zms_ate)`를 사용하여:

1. free space 산술 계산이 실제 ZMS 동작과 불일치
2. `zassert_equal(ZMS_DATA_IN_ATE_SIZE, ...)` — 정렬 패딩으로 인해 정확히 8바이트로 떨어지지 않음
3. VLA 버퍼가 큰 섹터 크기에서 스택 오버플로 유발

ZMS 구현 자체는 정상. 테스트 로직 버그.

## 수정 내용

| 변경 항목 | Before | After |
|-----------|--------|-------|
| ATE 크기 | `sizeof(struct zms_ate)` | `fixture->fs.ate_size` |
| free space 검증 | `zassert_equal(ZMS_DATA_IN_ATE_SIZE, ...)` | `>= ZMS_DATA_IN_ATE_SIZE && < ZMS_DATA_IN_ATE_SIZE + wbs` |
| 버퍼 할당 | VLA (스택) | `k_malloc`/`k_free` (힙) |
| 설정 | — | `CONFIG_HEAP_MEM_POOL_SIZE=65536` 추가 |

## 활동 로그

- **2026-02-26**: 이슈 분석 시작. `qemu_x86`에서 8KB 섹터 오버레이로 assertion 실패 재현.
- **2026-02-27**: Option A(테스트 전용 수정) 적용. `qemu_x86` 기본 설정에서 8/8 configurations, 107/107 test cases 통과 확인.
- **2026-02-27**: [PR #104644](https://github.com/zephyrproject-rtos/zephyr/pull/104644) 제출.
