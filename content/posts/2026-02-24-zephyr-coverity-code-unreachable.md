---
title: "Zephyr RTOS: CODE_UNREACHABLE 매크로의 Coverity Dead Code 오탐 분석"
date: 2026-02-24T12:00:00+09:00
description: "Zephyr의 CODE_UNREACHABLE 매크로에서 발생하는 Coverity dead code false positive 문제를 분석하고 해결 방안을 제시합니다."
categories: ["Zephyr", "Tech"]
tags: ["Zephyr", "Coverity", "Static Analysis", "C Preprocessor", "Open Source"]
draft: false
---

## 문제 요약

Zephyr RTOS의 `CODE_UNREACHABLE` 매크로(`__builtin_unreachable()`)가 Coverity 정적 분석에서 dead code로 오탐되는 문제. 매크로가 ~170곳에서 사용되어 개별 수정은 비현실적이며, 매크로 내부에 주석(`/* coverity[deadcode] */`)을 삽입하는 제안도 C 전처리기(Phase 3)에서 주석이 소실되어 작동하지 않음을 확인.

- **원본 이슈**: [zephyrproject-rtos/zephyr#99981](https://github.com/zephyrproject-rtos/zephyr/issues/99981)

## 분석 결과

Coverity 유저 모델을 통해 `__builtin_unreachable()`를 kill path(`__coverity_panic__()`)로 정의하면, 소스 코드 수정 없이 전역적으로 오탐을 제거할 수 있음.

## 활동 로그

- **2026-02-24**: 분석 결과를 기반으로 Coverity 유저 모델 제안 [코멘트](https://github.com/zephyrproject-rtos/zephyr/issues/99981#issuecomment-3948652255) 작성.
