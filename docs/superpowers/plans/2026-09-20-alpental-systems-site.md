# Alpental Systems Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the personal blog on `seyoungjeong.github.io`'s `main` branch with a small, themeless Hugo landing page for Alpental Systems (알펜탈 시스템즈), built by the existing Cloudflare Pages pipeline and served at `alpentalsystems.com`, while preserving the blog on a `blog-archive` branch and turning off GitHub Pages for this repo.

**Architecture:** A single-page, themeless Hugo site — one `hugo.toml`, one `layouts/index.html` template (with a `head.html` partial) rendering every section directly (no `content/` files needed for the home page), and one `static/css/style.css` stylesheet. No JS, no theme submodule, no build tooling beyond Hugo itself.

**Tech Stack:** Hugo (static site generator, no theme), plain CSS, Cloudflare Pages (build command `hugo`, output `public/`, already configured by the repo owner outside this repo).

**Spec:** `docs/superpowers/specs/2026-09-20-alpental-systems-site-design.md`

## Global Constraints

- Do not rewrite git history or force-push. The blog's history must remain reachable both via `blog-archive` and via `main`'s own pre-migration log.
- Korean only, no English copy on the page.
- No contact form — `mailto:contact@alpentalsystems.com` only.
- No business-registration footer block.
- Cloudflare's build command is exactly `hugo` (not `hugo --gc --minify`) — verify with that exact command.
- `.github/dependabot.yml` is out of scope — only `.github/workflows/hugo.yaml` is removed.
- Two steps require explicit, in-the-moment go-ahead from the repo owner before executing, even though the overall migration was already approved: turning off GitHub Pages (Task 5) and `git push origin main` (Task 6). Do not run those commands until the owner responds to the specific prompt in that task.

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `hugo.toml` | create | Site config: baseURL, language, title, tagline/email params |
| `layouts/partials/head.html` | create | `<head>` block: charset, viewport, title, meta description, stylesheet link |
| `layouts/index.html` | create | Full page markup: header/nav, hero, 소개, 서비스, 기술 스택, 경력, 문의, footer |
| `static/css/style.css` | create | All page styling, mobile-responsive |
| `README.md` | modify | Replace blog description with Hugo/Cloudflare site note |
| `.gitignore` | modify | Drop `_multiconfig.yml` (unused), add `.hugo_build.lock` |
| `archetypes/`, `assets/`, `config.toml`, `content/`, `layouts/` (old blog layouts), `static/` (old blog static), `themes/`, `.gitmodules`, `.hugo_build.lock` (tracked file), `.vscode/`, `.github/workflows/hugo.yaml` | delete | Blog-specific; removed from `main`, preserved on `blog-archive` |

---

### Task 1: Snapshot pending work and create the blog backup branch

**Files:** none created/modified — commits the working tree exactly as it currently stands.

**Interfaces:**
- Produces: branch `blog-archive` (local and pushed to `origin`), pointing at a commit that is a strict superset of the current `main` tip (includes today's pending edits).

- [ ] **Step 1: Confirm the expected pending changes**

Run: `git status`

Expected output (order may vary):
```
 M .gitignore
 M content/.obsidian/workspace.json
?? .obsidian/app.json
?? .obsidian/appearance.json
?? .obsidian/core-plugins.json
?? .obsidian/workspace.json
?? AGENTS.md
?? CLAUDE.md
?? GEMINI.md
?? Untitled.md
```
If the output differs (extra files, missing files), stop and report the diff before continuing — do not guess.

- [ ] **Step 2: Stage everything**

Run: `git add -A`

- [ ] **Step 3: Review what's staged before committing**

Run: `git status` and `git diff --cached --stat`

Confirm no unexpected files (secrets, credentials, build artifacts) are staged. All files listed in Step 1 should now show as staged additions/modifications.

- [ ] **Step 4: Commit the snapshot**

```bash
git commit -m "chore: snapshot pending blog notes before company site migration"
```

- [ ] **Step 5: Create the backup branch**

```bash
git branch blog-archive
```

- [ ] **Step 6: Push the backup branch to origin**

```bash
git push -u origin blog-archive
```

- [ ] **Step 7: Verify the backup**

Run: `git rev-parse main` and `git rev-parse blog-archive` — they must print the same commit hash. Run `git rev-parse origin/blog-archive` — must also match.

---

### Task 2: Remove blog-specific files from `main`

**Files:**
- Delete: `archetypes/`, `assets/`, `config.toml`, `content/`, `layouts/`, `static/`, `themes/` (submodule `hugo-bearblog`), `.gitmodules`, `.hugo_build.lock`, `.vscode/`, `.github/workflows/hugo.yaml`

**Interfaces:**
- Consumes: the commit created in Task 1 (this task starts from a clean, fully-backed-up working tree).
- Produces: a `main` working tree containing only non-blog files (`.git/`, `.gitignore`, `.github/dependabot.yml`, `README.md`, `docs/`, and untouched local-only untracked files like `.obsidian/` are now committed from Task 1 so they stay too — this task does not touch them).

- [ ] **Step 1: Deinit the theme submodule**

```bash
git submodule deinit -f themes/hugo-bearblog
```

- [ ] **Step 2: Remove the tracked blog paths**

```bash
git rm -r archetypes assets config.toml content layouts static themes .gitmodules .hugo_build.lock .vscode .github/workflows/hugo.yaml
```

- [ ] **Step 3: Verify only expected deletions are staged**

Run: `git status`

Expected: every path from Step 2 shows as deleted (`D`), nothing else changed. `.github/dependabot.yml` must NOT appear as deleted.

- [ ] **Step 4: Commit the removal**

```bash
git commit -m "chore: remove blog site, preserved on blog-archive branch"
```

---

### Task 3: Build the Alpental Systems page

**Files:**
- Create: `hugo.toml`
- Create: `layouts/partials/head.html`
- Create: `layouts/index.html`
- Create: `static/css/style.css`

**Interfaces:**
- Consumes: `.Site.Title`, `.Site.Params.tagline`, `.Site.Params.contactEmail` (defined in `hugo.toml`, read by `layouts/index.html` and `layouts/partials/head.html`).
- Produces: `public/index.html` and `public/css/style.css` when built with `hugo`.

- [ ] **Step 1: Write the site config**

Create `hugo.toml`:

```toml
baseURL = "https://alpentalsystems.com/"
languageCode = "ko-KR"
title = "알펜탈 시스템즈"
disableKinds = ["taxonomy", "term"]

[params]
  tagline = "임베디드 시스템을 위한 토탈 엔지니어링 솔루션"
  contactEmail = "contact@alpentalsystems.com"
```

`disableKinds` prevents Hugo's default category/tag taxonomy generation,
which this single-page site has no content for; without it, `hugo` emits
a "found no layout file for kind taxonomy" warning even though the build
still succeeds. Confirmed by a prior review's isolated test: adding this
line drops the page count from 5 to 3 and removes that warning.

- [ ] **Step 2: Write the head partial**

Create `layouts/partials/head.html`:

```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ .Site.Title }}</title>
  <meta name="description" content="{{ .Site.Params.tagline }}">
  <link rel="stylesheet" href="{{ "css/style.css" | relURL }}">
</head>
```

- [ ] **Step 3: Write the home page template**

Create `layouts/index.html`:

```html
<!DOCTYPE html>
<html lang="ko">
{{ partial "head.html" . }}
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="wordmark" href="#top">알펜탈 시스템즈</a>
      <nav class="nav">
        <a href="#about">소개</a>
        <a href="#services">서비스</a>
        <a href="#tech-stack">기술 스택</a>
        <a href="#track-record">경력</a>
        <a href="#contact">문의</a>
      </nav>
    </div>
  </header>

  <main id="top">
    <section class="hero">
      <div class="container">
        <h1>{{ .Site.Params.tagline }}</h1>
        <p class="hero-sub">스마트폰부터 위성 비행 컴퓨터까지, 미국 빅테크 경험을 포함해 20년 이상의 실전 경험을 기반으로 한 임베디드 엔지니어링 전문 기업입니다.</p>
        <a class="cta" href="#contact">문의하기</a>
      </div>
    </section>

    <section id="about" class="section">
      <div class="container">
        <h2>소개</h2>
        <p>알펜탈 시스템즈는 임베디드 펌웨어, RTOS, 디바이스 드라이버 분야에서 20년 이상의 실무 경험을 바탕으로 설립된 엔지니어링 기업입니다. 스마트폰 플랫폼(Android)부터 위성 비행 컴퓨터 시스템, 드론 배터리 관리 시스템, 무선 통신 전력 최적화까지 항공우주와 소비자 가전을 아우르는 다양한 프로젝트를 수행해 왔습니다.</p>
        <p>시스템 브링업부터 양산 배포까지 전 과정을 책임지는 실전 중심의 솔루션을 제공합니다.</p>
      </div>
    </section>

    <section id="services" class="section alt">
      <div class="container">
        <h2>서비스</h2>
        <div class="cards">
          <div class="card">
            <h3>RTOS·펌웨어 개발</h3>
            <p>Zephyr, RIOT-OS 등 오픈소스 RTOS 기반의 펌웨어 설계 및 구현</p>
          </div>
          <div class="card">
            <h3>디바이스 드라이버 개발</h3>
            <p>I2C, SPI, UART, USB, PCIe, CAN 등 다양한 인터페이스 드라이버 개발</p>
          </div>
          <div class="card">
            <h3>시스템 브링업 &amp; 트러블슈팅</h3>
            <p>SoC/FPGA 플랫폼의 초기 부팅 및 하드웨어 통합 문제 해결</p>
          </div>
          <div class="card">
            <h3>보안 부트로더 &amp; 인증</h3>
            <p>안전한 부트로더 설계 및 인증 메커니즘 구현</p>
          </div>
          <div class="card">
            <h3>전력 최적화 &amp; 성능 분석</h3>
            <p>저전력 설계 및 시스템 성능 프로파일링</p>
          </div>
          <div class="card">
            <h3>CI/CD &amp; 테스트 인프라</h3>
            <p>임베디드 플랫폼을 위한 빌드 자동화 및 테스트 인프라 구축</p>
          </div>
          <div class="card">
            <h3>임베디드 리눅스 (Yocto)</h3>
            <p>Yocto Project 기반 커스텀 리눅스 배포판 구축 및 BSP 개발</p>
          </div>
          <div class="card">
            <h3>로봇 소프트웨어 (ROS)</h3>
            <p>ROS/ROS2 기반 로봇 소프트웨어 설계 및 시스템 통합</p>
          </div>
        </div>
      </div>
    </section>

    <section id="tech-stack" class="section">
      <div class="container">
        <h2>기술 스택</h2>
        <ul class="tags">
          <li>C</li>
          <li>C++</li>
          <li>Python</li>
          <li>Java</li>
          <li>C#</li>
          <li>AWS</li>
          <li>Zephyr RTOS</li>
          <li>RIOT-OS</li>
          <li>Embedded Linux (Yocto)</li>
          <li>Android</li>
          <li>ROS/ROS2</li>
          <li>I2C</li>
          <li>SPI</li>
          <li>UART</li>
          <li>USB</li>
          <li>PCIe</li>
          <li>CAN</li>
        </ul>
      </div>
    </section>

    <section id="track-record" class="section alt">
      <div class="container">
        <h2>경력</h2>
        <ul class="timeline">
          <li>
            <h3>Amazon (시애틀, 미국)</h3>
            <p>Project Kuiper 위성 비행 컴퓨터 시스템, Prime Air 드론 배터리 관리 및 비행 제어 시스템, 보안 부트로더 개발</p>
          </li>
          <li>
            <h3>Microsoft (시애틀, 미국)</h3>
            <p>IEEE 802.11mc 기반 실내 측위 시스템, Windows 디바이스 드라이버(KMDF/UMDF) 개발</p>
          </li>
          <li>
            <h3>Qualcomm (샌디에이고, 미국)</h3>
            <p>802.11ad WLAN 전력 최적화, PCIe 드라이버 개발, 저전력 Wi-Fi 펌웨어 설계</p>
          </li>
          <li>
            <h3>Samsung Electronics (수원, 대한민국)</h3>
            <p>스마트폰 플랫폼 소프트웨어 개발 (Android)</p>
          </li>
        </ul>
      </div>
    </section>

    <section id="contact" class="section">
      <div class="container">
        <h2>문의</h2>
        <p>프로젝트 문의는 이메일로 연락해 주세요.</p>
        <a class="cta" href="mailto:{{ .Site.Params.contactEmail }}">{{ .Site.Params.contactEmail }}</a>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; 2026 Alpental Systems. All rights reserved.</p>
    </div>
  </footer>
</body>
</html>
```

- [ ] **Step 4: Write the stylesheet**

Create `static/css/style.css`:

```css
:root {
  --color-bg: #ffffff;
  --color-bg-alt: #f5f7fa;
  --color-text: #1a1f29;
  --color-text-muted: #4b5563;
  --color-accent: #2952cc;
  --color-border: #e2e5eb;
  --max-width: 960px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic", sans-serif;
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
}

.container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 24px;
}

.site-header {
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  background: var(--color-bg);
  z-index: 10;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.wordmark {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-text);
  text-decoration: none;
}

.nav a {
  margin-left: 24px;
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.95rem;
}

.nav a:hover {
  color: var(--color-accent);
}

.hero {
  padding: 96px 0 72px;
  text-align: center;
}

.hero h1 {
  font-size: 2.2rem;
  margin: 0 0 16px;
}

.hero-sub {
  color: var(--color-text-muted);
  max-width: 640px;
  margin: 0 auto 32px;
}

.cta {
  display: inline-block;
  padding: 12px 28px;
  background: var(--color-accent);
  color: #fff;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 600;
}

.section {
  padding: 64px 0;
}

.section.alt {
  background: var(--color-bg-alt);
}

.section h2 {
  font-size: 1.6rem;
  margin-bottom: 32px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
}

.card h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
}

.card p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 24px;
}

.timeline li {
  border-left: 3px solid var(--color-accent);
  padding-left: 20px;
}

.timeline h3 {
  margin: 0 0 4px;
  font-size: 1.1rem;
}

.timeline p {
  margin: 0;
  color: var(--color-text-muted);
}

.tags {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tags li {
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 6px 16px;
  font-size: 0.9rem;
  color: var(--color-text);
}

.site-footer {
  padding: 32px 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  border-top: 1px solid var(--color-border);
}

@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    height: auto;
    padding: 12px 0;
    gap: 8px;
  }
  .nav a {
    margin: 0 10px;
  }
  .hero {
    padding: 64px 0 48px;
  }
  .hero h1 {
    font-size: 1.6rem;
  }
}
```

- [ ] **Step 5: Build and verify with the exact Cloudflare command**

Run: `hugo`

Expected: build succeeds with `0 errors`, `0 warnings` shown in the summary, and `public/index.html` and `public/css/style.css` exist.

- [ ] **Step 6: Visual check in a browser**

```bash
hugo server -D
```

Using `claude-in-chrome` (or manually), open `http://localhost:1313/` and verify:
- All five sections (소개/서비스/기술 스택/경력/문의) render with the copy above
- Clicking each nav link scrolls to the right section
- The tech-stack tags wrap cleanly and the track record shows all four
  companies in order (Amazon, Microsoft, Qualcomm, Samsung Electronics)
- The "문의하기" and contact email buttons are visible and styled
- Resizing to a ~375px-wide viewport collapses the header to a stacked layout with no horizontal scroll
- No errors in the browser console

Stop the server (`Ctrl+C`) once confirmed.

- [ ] **Step 7: Commit**

```bash
git add hugo.toml layouts static
git commit -m "feat: build Alpental Systems landing page"
```

---

### Task 4: Update README and .gitignore

**Files:**
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:** none — documentation and tooling config only.

- [ ] **Step 1: Replace README.md**

Replace the full contents of `README.md` with:

```markdown
# alpentalsystems.com

Hugo site for Alpental Systems (알펜탈 시스템즈), built and deployed by
Cloudflare Pages (`hugo` build command, `public/` output).

## Local preview

    hugo server -D

## Production build

    hugo
```

- [ ] **Step 2: Update .gitignore**

Replace the full contents of `.gitignore` with:

```
.DS_Store
Thumbs.db
db.json
*.log
node_modules/
public/
.deploy*/
.hugo_build.lock
.claude/
.aider*
```

- [ ] **Step 3: Verify**

Run: `git status` — only `README.md` and `.gitignore` should show as modified.

- [ ] **Step 4: Commit**

```bash
git add README.md .gitignore
git commit -m "docs: update README and gitignore for the new site"
```

---

### Task 5: Turn off GitHub Pages for this repo

**Files:** none — this is a GitHub repo-settings change via API, not a git operation.

**Interfaces:** none.

- [ ] **Step 1: Confirm with the owner before running anything**

Ask explicitly: "Ready to turn off GitHub Pages for `seyoungjeong/seyoungjeong.github.io`? This will make `https://seyoungjeong.github.io` stop resolving to anything. Confirm to proceed." Do not run Step 2 until the owner says yes in this session.

- [ ] **Step 2: Delete the Pages configuration**

```bash
gh api -X DELETE repos/seyoungjeong/seyoungjeong.github.io/pages
```

- [ ] **Step 3: Verify**

```bash
gh api repos/seyoungjeong/seyoungjeong.github.io/pages
```

Expected: a 404 / "Not Found" response, confirming Pages is disabled.

---

### Task 6: Push `main` and verify the live site

**Files:** none.

**Interfaces:** none.

- [ ] **Step 1: Confirm with the owner before pushing**

Ask explicitly: "Ready to push `main`? This is what Cloudflare Pages will build and serve at alpentalsystems.com. Confirm to proceed." Do not run Step 2 until the owner says yes in this session.

- [ ] **Step 2: Push**

```bash
git push origin main
```

- [ ] **Step 3: Verify the backup branch and main history are both intact**

```bash
git log --oneline -5
git log --oneline blog-archive -5
```

Confirm `main`'s log shows the new migration commits on top, and `blog-archive`'s log still ends at the pre-migration snapshot commit from Task 1.

- [ ] **Step 4: Report to the owner**

Tell the owner the push is done and that Cloudflare Pages should now be building; ask them to check their Cloudflare dashboard for build status (this session cannot see Cloudflare's build logs).

---

## Self-Review Notes

- **Spec coverage:** Migration plan (Task 1-2, 5-6), site architecture (Task 3), copy including the Yocto/ROS services, the removed 오픈소스 기여 item, the 20-year/Samsung Electronics revision, and the new 기술 스택 section (Task 3, matches revised spec), README/.gitignore (Task 4), verification plan (Task 3 Steps 5-6, Task 6 Step 3) — all spec sections have a corresponding task.
- **Placeholder scan:** no TBD/TODO; all file contents are complete and final, not summarized.
- **Type/name consistency:** `.Site.Params.tagline` and `.Site.Params.contactEmail` are defined in Task 3 Step 1 (`hugo.toml`) and consumed identically in Task 3 Steps 2-3 (`head.html`, `index.html`) — no mismatches.
