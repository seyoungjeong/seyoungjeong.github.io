---
title: "STM32F3 Discovery와 Zephyr로 기울기 보정 나침반 만들기"
date: 2026-09-25
description: "STM32F3 Discovery 보드의 가속도/지자기 센서를 Zephyr로 읽고, 기울기 보정과 캘리브레이션을 거쳐 8개 LED로 방위를 표시합니다."
summary_en: >
  This post builds a tilt-compensated compass on the STM32F3 Discovery board
  with Zephyr RTOS. It covers identifying the board revision and its sensors,
  handling the difference in the devicetree, reading the accelerometer and
  magnetometer through Zephyr's sensor API, computing heading with tilt
  compensation, and hard-iron calibration. Logic analyzer captures of the
  sensor bus and before/after calibration results are included.
repo: ""
draft: true
---

## 보드 리비전과 센서 확인

## 개발 환경 구축 (west, Zephyr SDK)

## 센서 값 읽기 (디바이스 트리, sensor shell)

## 방위각 계산과 기울기 보정

## Hard-iron 캘리브레이션: 보정 전후 비교

## 버스 파형 측정 (I2C/SPI)

## 결과와 다음 단계
