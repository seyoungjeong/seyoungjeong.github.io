---
title: "Netlify에서 GitHub Pages로 호스팅 환경 이전 및 Hugo 트러블슈팅"
date: 2026-02-20T20:00:00+09:00
description: "Netlify에서 GitHub Pages 및 Actions 기반으로 호스팅을 이전하는 절차와 관련 Hugo 빌드 에러 해결 방법에 대해 설명합니다."
categories: ["Blog", "Tech"]
tags: ["Hugo", "GitHub Pages", "GitHub Actions", "Netlify", "Decap CMS", "PaperMod", "Troubleshooting"]
draft: false
---

## 1. 개요 및 이전 배경

과도한 트래픽 및 빌드 시간 제한에 따른 유지보수 측면의 오버헤드를 줄이고자, 기존 사용 중이던 호스팅 및 CMS 환경(Netlify + Decap CMS)을 제거하고 GitHub Actions와 GitHub Pages 기반의 인프라로 사이트 이전을 진행했습니다. 본 문서에서는 마이그레이션 절차와 서버 빌드 파이프라인 전환 중 발생한 에러 현상 및 해결 방법을 요약합니다.

### 1.1. 호스팅 환경 비교 (Netlify + Decap CMS vs. GitHub Pages + Actions)

| 구분 | Netlify + Decap CMS | GitHub Pages + Actions |
| :--- | :--- | :--- |
| **비용 구조** | 무료 티어 초과 시 과금 발생 (Bandwidth, Build limits) | 완전 무료 (개인 리포지토리 기준 사실상 무제한) |
| **콘텐츠 관리** | 브라우저 기반 CMS UI 제공 | 로컬 에디터 및 CLI 명령어로 직접 관리 |
| **권한 및 인증** | Netlify Identity / Git Gateway 기반 인증 | 별도 CMS 인증 불필요 (GitHub 계정 자체 권한) |
| **빌드 파이프라인** | Netlify 내부 CI/CD 자동화 빌드 | GitHub Actions YAML 파일을 통한 수동 제어 및 커스터마이징 |
| **유지보수 관점** | 서드파티 서비스 의존성 존재 및 버그 추적 어려움 | 모든 빌드 로그 및 파이프라인이 GitHub 내로 통합됨 |

---

## 2. 호스팅 마이그레이션 절차

마이그레이션 작업은 Netlify 종속성을 제거하고 GitHub Actions가 주도하는 배포 환경을 구성하는 데 초점을 두었습니다.

### 2.1. 기존 시스템 파일 제거
Netlify 및 Decap CMS와 연동되는 모든 구성 요소를 삭제 및 수정했습니다.
- `netlify.toml` 삭제 (Netlify 빌드 설정)
- `static/admin/config.yml` 및 `index.html` 파일 삭제 (Decap CMS 접속용)
- Hugo 설정 파일(`config.toml`) 내 `baseURL` 값을 GitHub Pages 포맷(`https://[사용자명].github.io/`)으로 변경

### 2.2. GitHub Actions 자동 배포 구성
Main 브랜치에 코드가 푸시되면 자동으로 Hugo 프로젝트를 컴파일하고 GitHub Pages로 배포하도록 `.github/workflows/hugo.yaml` 워크플로우를 신규 생성했습니다. CMS 환경을 배제하고 로컬 Markdown 에디팅을 통해 콘텐츠를 작성한 뒤 `git push` 명령어만으로 배포 처리가 이루어집니다.

---

## 3. 트러블슈팅

GitHub Actions 빌드 과정에서 발생한 주요 장애 요인과 조치 내역입니다.

### 3.1. GitHub Actions 워크플로우 `NPM ENOENT` 에러
GitHub Pages의 배포 액션 템플릿이 Node.js 환경을 셋업하는 과정에서 프로젝트 루트에 `package.json` 파일이 존재하지 않아 `npm install` 스크립트 실행이 실패하며 `ENOENT` 에러를 반환했습니다.
* **해결 방법**: `dependencies` 항목이 비어있는 더미 `package.json` 형태의 파일을 수동으로 생성하여 Node 패키지 매니저의 인스톨 프로세스가 오류 없이 종료되도록 우회 처리했습니다.

### 3.2. Hugo PaperMod 테마 관련 `Missing Partials` 렌더링 에러
GitHub Actions 환경 내에서 사이트가 빌드될 때 다음 두 가지 템플릿 에러가 발생했습니다.
- `partial "google_analytics.html" not found`
- `can't evaluate field LanguageCode in type *langs.Language`

**원인 분석**: 사용 중인 PaperMod 테마 릴리즈 버전이 갱신되면서 기능이 변경되었으며, 연계하여 코어 컴파일러인 `Hugo v0.146.0+` 이상을 최소 요구 버전으로 제한한 것이 원인이었습니다.

**해결 방법**:
1. **버전 수정**: GitHub Actions 워크플로우(`hugo.yaml`) 내 설정된 빌드 런타임 변수인 `HUGO_VERSION`을 `0.146.0`으로 스펙업했습니다.
2. **레이아웃 오버라이드**: Git Submodule 내부에서 직접 코드를 수정하는 대신, 누락 오류가 발생하는 `google_analytics.html` 템플릿과 메타데이터 구문을 프로젝트 최상단의 `layouts/partials/` 위치에 선언하여 강제 오버라이드(override) 되도록 조치했습니다.

---

## 4. 트래킹 시스템 설정 재매핑 (Google Analytics / Search Console)

운영 도메인이 `.github.io`로 변경됨에 따라 통계 수집 시스템 설정을 다음과 같이 동기화했습니다.

* **Google Analytics (GA4)**: 속성 및 데이터 스트림 설정에서 추적 웹사이트의 URL을 신규 도메인 주소로 변경했습니다. (Tracking ID는 기존과 동일하게 유지)
* **Google Search Console**: `config.toml` 내 변경된 `baseURL`로 인해 Hugo 빌드 시 사이트맵(`sitemap.xml`) 내부 URL이 신규 주소로 정상 재생성됩니다. 구글 서치콘솔 측에 신규 도메인 속성을 추가하고 새로 생성된 `sitemap.xml` 경로를 제출하여 인덱싱을 갱신했습니다.

---

*이 글은 Google의 Antigravity 에이전트의 도움을 받아 작성되었습니다.*
