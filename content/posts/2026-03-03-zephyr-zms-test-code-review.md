---
title: "Zephyr RTOS: ZMS free space 테스트 코드 리뷰 및 개선"
date: 2026-03-03T19:00:00+09:00
description: "ZMS free space 테스트의 코드 품질 문제(magic number, 변수 명명, 매크로 스코프, O(N²) 성능)를 발견하고 수정한 기록."
categories: ["Coding"]
tags: ["Zephyr", "Open Source", "Code Review", "Contributing"]
draft: false
---

PR [#104644](https://github.com/zephyrproject-rtos/zephyr/pull/104644) 리뷰 과정에서 발견한 코드 품질 문제들과 수정 내용.

---

## 1. `sizeof(struct zms_ate)` → `fixture->fs.ate_size`

**문제**: Flash의 `write_block_size`에 따라 ZMS는 ATE를 `ROUND_UP(sizeof(struct zms_ate), write_block_size)` 크기로 배치한다. 테스트가 컴파일 타임 `sizeof`를 직접 사용하면 `write_block_size > sizeof(struct zms_ate)` 인 환경에서 free space 계산이 어긋난다.

```c
/* before */
const size_t max_space_in_sector = fixture->fs.sector_size - sizeof(struct zms_ate) * 5;

/* after */
ate_size = fixture->fs.ate_size;  /* runtime: ROUND_UP(sizeof(zms_ate), wbs) */
max_space_in_sector = fixture->fs.sector_size - ate_size * ZMS_MIN_ATE_NUM;
```

---

## 2. Magic number `5` → `ZMS_MIN_ATE_NUM`

**문제**: 섹터에 예약되는 ATE 슬롯 수가 `5`로 하드코딩되어 있었음. `zms_priv.h`에 이미 `ZMS_MIN_ATE_NUM = 5` (close / empty / gc_done / delete / data)가 정의되어 있음.

```c
/* before */
fixture->fs.sector_size - ate_size * 5;

/* after */
fixture->fs.sector_size - ate_size * ZMS_MIN_ATE_NUM;
```

---

## 3. `wbs` → `write_block_size`

**문제**: 로컬 변수명 `wbs`가 ZMS 구현 코드의 관행(`write_block_size` 풀네임)과 불일치.

```c
/* before */
size_t wbs;
wbs = fixture->fs.flash_parameters->write_block_size;

/* after */
size_t write_block_size;
write_block_size = fixture->fs.flash_parameters->write_block_size;
```

---

## 4. 변수 선언 위치 정리

**문제**: `const size_t max_space_in_sector`, `char *write_buf`, `ssize_t fs_sector/fs_total` 등이 함수 중간이나 내부 `{ }` 블록 안에 선언되어 있었음. Zephyr 테스트 코드 관행은 모든 변수를 함수 상단에 선언.

`{ }` 블록은 원래 C89 호환을 위해 중간에 변수를 선언하는 우회책이었는데, Zephyr는 C99 이상을 사용하면서도 관행적으로 함수 상단 선언을 유지하고 있음.

---

## 5. `_al()` 매크로 정리

**문제**: `test_zms_free_space_5sectors`에서 `#define _al(len) ROUND_UP((len), write_block_size)`를 함수 내부에 선언하고 `#undef`로 해제했음. 이후 파일 상단으로 옮겼지만, 로컬 변수 `write_block_size`에 의존하는 매크로를 파일 스코프에 두는 것은 오히려 혼란스러움.

**최종 결론**: 매크로 자체를 제거하고 `ROUND_UP(len, write_block_size)`를 직접 사용.

```c
/* before */
#define _al(len) ROUND_UP((len), write_block_size)
free_space_total -= (_al(100) + _al(200) + _al(300) + 3 * ate_size);

/* after */
free_space_total -= (ROUND_UP(100, write_block_size) +
                     ROUND_UP(200, write_block_size) +
                     ROUND_UP(300, write_block_size) + 3 * ate_size);
```

---

## 6. O(N²) 성능 문제 수정

**문제**: `test_zms_free_space`의 outer `do-while` loop가 매 iteration마다 섹터를 꽉 채우고 삭제하는 패턴을 반복. 섹터를 꽉 채울 때마다 ZMS가 GC를 트리거하며, GC는 O(N) flash I/O (N = 섹터 내 ATE 수). Loop가 N번 돌면 총 O(N²). 8KiB 섹터(N≈512)에서 약 20분 소요됨.

**수정**: 중간 iteration들은 대형 entry를 쓰지 않고 1-byte entry를 바로 append하는 inner loop로 대체. GC를 불필요하게 반복 트리거하는 패턴을 제거.

```c
/*
 * Without this inner loop, the outer loop would trigger GC on
 * every iteration by filling and then deleting a full-sector
 * entry, resulting in O(N^2) flash I/O (N = sector_size /
 * ate_size). On hardware with 8KiB sectors this caused a
 * 20-minute test run.
 *
 * Instead, skip straight to writing small ATEs until only
 * 4 * ate_size of free space remains, letting the outer loop
 * handle the final iterations normally.
 */
while (free_space_total > 4 * ate_size) {
    len = zms_write(&fixture->fs, id, write_buf, 1);
    id++;
    free_space_sector -= ate_size;
    free_space_total -= ate_size;
}
```

---

## 결과

- PR: [zephyrproject-rtos/zephyr#104644](https://github.com/zephyrproject-rtos/zephyr/pull/104644)
- Branch: `fix/101880-zms-free-space-test`
