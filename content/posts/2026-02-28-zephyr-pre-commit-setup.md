---
title: "Zephyr RTOS: pre-commit 훅 기반 자동 검사 셋업"
date: 2026-02-28T17:55:00+09:00
description: "Zephyr 프로젝트 커밋 시 코드 포맷 및 커밋 메시지 규정 준수를 자동 검사하는 pre-commit 훅 설정 가이드."
categories: ["Zephyr", "Tech"]
tags: ["Zephyr", "Git", "pre-commit"]
draft: false
---

## 개요

Zephyr 프로젝트 기여 및 작업 시 커밋 메시지 규칙(`subsystem: 50자 이내 요약`)과 코드 포맷 검증 자동화를 위해 `pre-commit` 도구를 설정하는 방법 정리. 

저장소의 `.pre-commit-config.yaml` 룰을 적용하여 커밋 전 규정 위반을 자동 차단할 수 있음.

## 설치

시스템에 `pre-commit` 패키지 설치:

```bash
# macOS (Homebrew)
brew install pre-commit

# Python 환경
pip3 install pre-commit
```

## Zephyr 저장소 설정

로컬 Zephyr 경로(`~/ws/zephyr`)에서 Git Hook 적용:

```bash
cd ~/ws/zephyr

# 기본 훅 (코드 포맷, 스타일 체크) 설치
pre-commit install

# 커밋 메시지 규정 검사 훅 설치
pre-commit install --hook-type commit-msg
```

명령어 실행 후 `.git/hooks/` 경로에 훅 스크립트가 생성됨.

## 작동 방식

- `git commit` 실행 시 미리 정의된 룰(checkpatch, compliance 등)을 기반으로 변경 파일 자동 검사.
- **성공 (Passed)**: 검사 통과 시 커밋 완료.
- **실패 (Failed)**: 위반 사항 출력 후 커밋 취소. 오류 수정 후 재커밋 시도 필요.
