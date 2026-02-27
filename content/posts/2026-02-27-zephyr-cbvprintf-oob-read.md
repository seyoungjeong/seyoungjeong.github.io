---
title: "Zephyr RTOS: cbvprintf_package %.*s 포맷 사용 시 OOB 읽기 버그 분석"
date: 2026-02-27T14:40:00+09:00
description: "cbvprintf_package가 %.*s 포맷의 precision을 무시하고 strlen()을 호출하여 heap-buffer-overflow가 발생하는 문제를 분석한 기록입니다."
categories: ["Zephyr", "Tech"]
tags: ["Zephyr", "Open Source", "Bug Analysis", "Contributing"]
draft: false
---

## 문제 요약

`cbvprintf_package()`에서 `%.*s` 포맷 사용 시 precision specifier를 무시하고 `strlen()`을 호출. null-terminated가 아닌 문자열에서 힙 버퍼 오버플로(out-of-bounds read) 발생.

- **원본 이슈**: [zephyrproject-rtos/zephyr#93999](https://github.com/zephyrproject-rtos/zephyr/issues/93999)

## 원인 분석

`lib/os/cbprintf_packaged.c`의 포맷 문자열 파싱에서 `'.'`과 `'*'`를 별도로 처리하지만, `'*'`로 소비한 precision 정수 값을 저장하지 않음. 이후 `'s'` 처리 시 precision 정보 없이 `strlen(s)`를 호출하여 할당된 버퍼를 넘어서 읽음.

영향받는 코드:
- **Sizing pass** ([L676](https://github.com/zephyrproject-rtos/zephyr/blob/main/lib/os/cbprintf_packaged.c#L676)): `len += strlen(s) + 1 + 1;`
- **Copy pass** ([L792](https://github.com/zephyrproject-rtos/zephyr/blob/main/lib/os/cbprintf_packaged.c#L792)): `size = strlen(s) + 1;`

## 재현

macOS + Apple Clang + AddressSanitizer로 핵심 동작을 독립 재현:

```c
char *str = malloc(10);
memcpy(str, "Actual log", 10); /* null 종료 없음 */
strlen(str);                   /* cbvprintf_package L676과 동일한 호출 */
```

```
==68418==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000000fa
READ of size 11 at 0x6020000000fa thread T0
    #0 in strlen
0x6020000000fa is located 0 bytes after 10-byte region [0x6020000000f0,0x6020000000fa)
```

10바이트 버퍼에서 11바이트를 읽으려 하여 OOB 발생. 이슈에서 보고된 에러 패턴과 동일.

## 수정 방향

| 항목 | Before | After |
|------|--------|-------|
| precision 추적 | 없음 (`'.'`, `'*'` 값 버림) | `has_precision` / `str_precision` 변수로 추적 |
| 문자열 길이 계산 | `strlen(s)` | `strnlen(s, precision)` (precision 존재 시) |

## 활동 로그

- **2026-02-27**: 이슈 분석. 독립 ASAN 테스트로 OOB 재현 확인. 이슈에 root cause analysis 코멘트 작성.
