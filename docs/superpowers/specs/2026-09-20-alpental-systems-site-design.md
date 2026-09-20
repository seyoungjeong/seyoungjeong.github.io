# Alpental Systems company site — design

## Context

This repository (`seyoungjeong.github.io`) currently hosts a personal Hugo/PaperMod
blog, deployed to GitHub Pages via `.github/workflows/hugo.yaml`.

The owner is replacing this repository's `main` branch with a new company site
for 알펜탈 시스템즈 (Alpental Systems), a private, solo-owned company offering
embedded-systems engineering services, built on the owner's own career
background. Cloudflare Pages is already configured to build this same repo
with Hugo and serve it at `alpentalsystems.com`. GitHub Pages (currently
serving `seyoungjeong.github.io` with no custom domain) will be turned off.

The blog is not being deleted — it is preserved on a `blog-archive` branch.

## Goals

- Replace the blog on `main` with a small, themeless Hugo site for Alpental
  Systems, buildable by the existing Cloudflare Pages pipeline.
- Preserve the blog's full history (branch + `main`'s own log — no rewrite).
- Turn off GitHub Pages for this repo (it would otherwise mirror the same new
  content at `seyoungjeong.github.io`, which is undesired).
- Ship a single Korean-language landing page that reads as a credible,
  professional consulting/contracting site for embedded-systems work.

## Non-goals

- No multi-page site, no CMS, no build-time content pipeline beyond Hugo.
- No contact form (mailto link only).
- No business-registration legal footer (deferred until the entity is
  formalized).
- No English version (Korean only, per decision).
- No new visual identity/logo — text wordmark only for v1.

## Migration plan

Executed on `main` of `seyoungjeong.github.io`:

1. Commit whatever is currently pending in the working tree as-is (tracked
   edits to `.gitignore`/`content/.obsidian/workspace.json`, and untracked
   `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.obsidian/`, `Untitled.md`), so
   nothing in progress is lost.
2. Create branch `blog-archive` at that commit; push it to `origin`. This is
   the durable backup — the blog is also still reachable by walking `main`'s
   own history prior to the migration commit, since we do not rewrite
   history or force-push.
3. Remove blog-specific tracked files from `main`:
   `archetypes/`, `assets/`, `config.toml`, `content/`, `layouts/`,
   `static/`, `themes/` (submodule), `.gitmodules`, `.hugo_build.lock`,
   `.vscode/`, `.github/workflows/hugo.yaml`.
4. Add the new Hugo site (see Site architecture below).
5. Turn off GitHub Pages for the repo: delete the Pages configuration via
   `gh api -X DELETE repos/seyoungjeong/seyoungjeong.github.io/pages` (it is
   currently Actions-built with no custom domain). Confirm with the owner
   immediately before this call, since it changes live GitHub infrastructure.
6. Commit the new site to `main` with a conventional-commit message.
7. Stop and get explicit go-ahead from the owner before `git push origin
   main` — this is the step that changes what Cloudflare actually serves at
   `alpentalsystems.com`.

## Site architecture

Themeless Hugo site, no submodule:

- `hugo.toml` — `baseURL = "https://alpentalsystems.com/"`,
  `languageCode = "ko-KR"`, `title = "알펜탈 시스템즈"`.
- `layouts/index.html` — a single custom template rendering the entire page
  (Hugo generates the home page from this template with no content files
  required).
- `layouts/partials/head.html` — head tag (charset, viewport, title,
  meta description, stylesheet link).
- `static/css/style.css` — all styling.
- `static/favicon.svg` — simple text/monogram favicon (optional, can be
  added post-launch if not ready).
- `README.md` — replaced: short note that this is a Hugo site built by
  Cloudflare Pages for Alpental Systems.
- `.gitignore` — drop Hugo-specific entries that no longer apply
  (`_multiconfig.yml`), keep `public/`, `.DS_Store`, `.aider*`, `.claude/`.
  `.hugo_build.lock` should be ignored rather than tracked.

No `content/` directory, no theme, no JS framework, no analytics (can be
added later if requested).

## Page structure and copy (Korean)

Single scrolling page, anchor nav: 소개 / 서비스 / 경력 / 문의.

**Header**
- Wordmark: "알펜탈 시스템즈"
- Nav links to the anchors below

**Hero**
- H1: "임베디드 시스템을 위한 토탈 엔지니어링 솔루션"
- Subline: "위성 비행 컴퓨터부터 저전력 무선 시스템까지, 10년 이상의 실전
  경험을 기반으로 한 임베디드 엔지니어링 전문 기업입니다."
- CTA button → scrolls to 문의, label "문의하기"

**소개 (About)**
> 알펜탈 시스템즈는 임베디드 펌웨어, RTOS, 디바이스 드라이버 분야에서 10년
> 이상의 실무 경험을 바탕으로 설립된 엔지니어링 기업입니다. 위성 비행
> 컴퓨터 시스템, 드론 배터리 관리 시스템, 무선 통신 전력 최적화 등
> 항공우주와 소비자 가전을 아우르는 다양한 프로젝트를 수행해 왔습니다.
>
> Zephyr RTOS, RIOT-OS 등 오픈소스 프로젝트에 대한 활발한 기여를 통해
> 검증된 기술력을 보유하고 있으며, 시스템 브링업부터 양산 배포까지 전
> 과정을 책임지는 실전 중심의 솔루션을 제공합니다.

**서비스 (Services)** — six cards, title + one-line description:

1. RTOS·펌웨어 개발 — Zephyr, RIOT-OS 등 오픈소스 RTOS 기반의 펌웨어 설계 및 구현
2. 디바이스 드라이버 개발 — I2C, SPI, UART, USB, PCIe, CAN 등 다양한 인터페이스 드라이버 개발
3. 시스템 브링업 & 트러블슈팅 — SoC/FPGA 플랫폼의 초기 부팅 및 하드웨어 통합 문제 해결
4. 보안 부트로더 & 인증 — 안전한 부트로더 설계 및 인증 메커니즘 구현
5. 전력 최적화 & 성능 분석 — 저전력 설계 및 시스템 성능 프로파일링
6. CI/CD & 테스트 인프라 — 임베디드 플랫폼을 위한 빌드 자동화 및 테스트 인프라 구축

**경력 (Track record)** — company/period, 1-2 line summary each; public
career history, matching what the owner already discloses on their resume:

- Amazon — Project Kuiper 위성 비행 컴퓨터 시스템, Prime Air 드론 배터리
  관리 및 비행 제어 시스템, 보안 부트로더 개발
- Qualcomm — 802.11ad WLAN 전력 최적화, PCIe 드라이버 개발, 저전력 Wi-Fi
  펌웨어 설계
- Microsoft — IEEE 802.11mc 기반 실내 측위 시스템, Windows 디바이스
  드라이버(KMDF/UMDF) 개발
- 오픈소스 기여 — Zephyr RTOS, RIOT-OS, llama.cpp에 다수의 머지된 기여
  (github.com/seyoungjeong)

**문의 (Contact)**
- "프로젝트 문의는 이메일로 연락해 주세요."
- `mailto:contact@alpentalsystems.com`

**Footer**
- "© 2026 Alpental Systems. All rights reserved." — no business-registration
  block.

## Visual design

Clean/corporate tone: light background, one accent color (blue/slate),
generous whitespace, system font stack (no webfont dependency, unlike the
blog's Pretendard). Mobile-responsive single column below ~768px.

## Manual steps for the owner (outside this repo/session)

- Confirm Cloudflare Pages build command/output directory still match a
  themeless Hugo build (`hugo --gc --minify`, output `public/`) — no
  submodule init needed now that `themes/` is removed.
- Confirm DNS for `alpentalsystems.com` points at Cloudflare (already done,
  per owner).
- Set up `contact@alpentalsystems.com` mailbox if not already active.

## Verification plan

- `hugo server -D` locally to preview the rendered page.
- Open in a browser via `claude-in-chrome` (or the local server) and check:
  layout at desktop and mobile widths, all anchor links scroll correctly,
  `mailto:` link is correct, no console errors.
- `hugo --gc --minify` production build succeeds with no errors/warnings.
- `git log` / `git branch` confirm `blog-archive` exists and matches
  pre-migration `main`.

## Risks / open items

- Turning off GitHub Pages and pushing `main` both change live, shared
  state — both require an explicit go-ahead in the same session, not implied
  by earlier approvals.
- Cloudflare's exact build settings are not visible from this repo; if the
  build command assumed a theme/submodule init step, removing `themes/` is
  still safe (Hugo builds fine with zero themes), but the owner should watch
  the first Cloudflare build after push in case of an unrelated pipeline
  assumption.
