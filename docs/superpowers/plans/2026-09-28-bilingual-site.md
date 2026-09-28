# English Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an English section at `/en/` (full landing page and a blog list built from each post's `summary_en`) with a language switch and `hreflang` tags, leaving the Korean site at `/` unchanged.

**Architecture:** Hugo multilingual mode with `ko` as the default language at the root and `en` under `/en/`. Landing page copy moves into `data/<lang>/home.yaml`; UI strings go to `i18n/<lang>.toml`. The English blog list reads the Korean posts through the posts section's Korean translation, so no English file is needed per post.

**Tech Stack:** Hugo extended (local v0.163.0; Cloudflare Pages builds with `hugo`), Go templates, plain CSS, Python 3 standard library for the link check.

**Spec:** `docs/superpowers/specs/2026-09-28-bilingual-site-design.md`

## Global Constraints

- Every existing Korean URL keeps working; Korean pages look the same.
- English section at `/en/`; `defaultContentLanguage = "ko"`, `defaultContentLanguageInSubdir = false`.
- No English page per post unless `index.en.md` exists.
- Use only long-standing Hugo features (`i18n`, `relLangURL`, `.Translations`, `.AllTranslations`, partials with `return`); do not use `hugo.Sites`, because the Cloudflare Pages Hugo version is not known.
- `hugo --gc --minify` must finish without `ERROR`; the existing `languageCode` deprecation `WARN` is accepted.
- Work on branch `feat/bilingual`; do not push until the owner has seen the preview.
- Commit messages: conventional commits, plain English, `Co-Authored-By` trailer.

## Refinements (approve with this plan)

1. **"Identical" means identical after minification.** Moving copy into loops changes whitespace and drops HTML comments in the unminified output but not the page. The copy-move check compares `hugo --gc --minify` builds of the Korean `index.html` byte for byte.
2. **Cloudflare's Hugo version** is unknown to this repo; the plan is verified with the local Hugo, and after the push the owner checks the Cloudflare Pages build log.

## Review Focus

1. **Translations of pages without content files:** the home page has no `content/_index.md`; the language switch and `hreflang` rely on Hugo linking both homes as translations. The link check must show a working switch on both homes.
2. **English pages reading Korean posts:** the English list and English home must list all four posts, with Korean titles and English summaries, and link to the Korean articles.
3. **Korean pages staying the same** through Tasks 2-4 (checked by comparing minified output).
4. **Anchors:** `/en/posts/#<slug>` must exist for every post, since Korean posts link there.
5. **Sitemaps:** every `<loc>` in the sitemap files must exist in the built site.

---

### Task 1: Link check script

**Files:**
- Create: `scripts/check-links.py`

- [ ] **Step 1: Write the script**

Create `scripts/check-links.py` (mode 755):

```python
#!/usr/bin/env python3
"""Checks internal links in a built Hugo site.

Usage: check-links.py PUBLIC_DIR BASE_URL
Every href/src inside the site and every sitemap <loc> must resolve to a
file, and a #fragment must exist as an id on the target page. Prints the
broken links and exits 1 if there are any.
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])


def target_file(public, path):
    p = os.path.join(public, unquote(path).lstrip("/"))
    if path.endswith("/") or os.path.isdir(p):
        p = os.path.join(p, "index.html")
    return os.path.normpath(p)


def main(public, base):
    host = urlparse(base).netloc
    pages, broken, checked = {}, [], 0
    for root, _, files in os.walk(public):
        for name in files:
            if name.endswith(".html"):
                path = os.path.normpath(os.path.join(root, name))
                parser = Page()
                with open(path, encoding="utf-8") as f:
                    parser.feed(f.read())
                pages[path] = parser
    sources = [(p, "/" + os.path.relpath(p, public).replace(os.sep, "/"), parser.links)
               for p, parser in pages.items()]
    for root, _, files in os.walk(public):
        for name in files:
            if name.endswith(".xml") and "sitemap" in name:
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    locs = re.findall(r"<loc>([^<]+)</loc>", f.read())
                sources.append((path, "/" + os.path.relpath(path, public), locs))
    for _, page_url, links in sources:
        for link in links:
            u = urlparse(urljoin(base.rstrip("/") + page_url, link))
            if u.scheme not in ("http", "https") or u.netloc != host:
                continue
            checked += 1
            f = target_file(public, u.path)
            if not os.path.exists(f):
                broken.append((page_url, link, "missing"))
            elif u.fragment and f in pages and u.fragment not in pages[f].ids:
                broken.append((page_url, link, "no id " + u.fragment))
    for b in broken:
        print("BROKEN %s -> %s (%s)" % b)
    print("%d pages, %d links checked, %d broken" % (len(pages), checked, len(broken)))
    return 1 if broken else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
```

- [ ] **Step 2: Check that it catches a broken link**

Run:
```bash
T=$(mktemp -d) && mkdir -p $T/a && printf '<a href="/missing/">x</a><a href="/a/#nope">y</a>' > $T/index.html && printf '<p id="yes">a</p>' > $T/a/index.html && python3 scripts/check-links.py $T https://example.com/; echo "exit=$?"; rm -rf $T
```
Expected: two `BROKEN` lines (`missing`, `no id nope`) and `exit=1`.

- [ ] **Step 3: Baseline on the current site**

Run: `hugo --gc --minify -d /tmp/rc-site-base >/dev/null && python3 scripts/check-links.py /tmp/rc-site-base https://alpentalsystems.com/`
Expected: `0 broken`.

- [ ] **Step 4: Commit**

```bash
git add scripts/check-links.py
git commit -m "build: add a link check for the built site" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Move the landing page copy into data (structural)

**Files:**
- Create: `data/ko/home.yaml`
- Modify: `layouts/index.html`

- [ ] **Step 1: Build the reference**

Run: `hugo --gc --minify -d /tmp/rc-site-before >/dev/null`

- [ ] **Step 2: Create `data/ko/home.yaml`**

```yaml
hero_sub: "미국 빅테크에서 쌓은 연구, 양산 경험을 기반으로 한 임베디드 토탈 솔루션을 제공합니다"

about:
  title: "소개"
  body: "알펜탈 시스템즈(Alpental Systems)는 설립자가 삼성전자, 미국의 아마존, 마이크로소프트, 퀄컴 등에서 소프트웨어 엔지니어로 쌓은 20여년의 임베디드 펌웨어, RTOS, 디바이스 드라이버 분야의 실무 경험을 바탕으로 설립된 엔지니어링 기업입니다. 위성 비행 컴퓨터 시스템, 드론 배터리 관리 시스템(BMS), FTS(Flight Termination System), WLAN SOC 전력 최적화, Windows 디바이스 드라이버 개발, AWS와 연동된 edge 디바이스의 데이터 처리, 양산 지원 까지 항공우주와 소비자 가전을 아우르는 다양한 프로젝트를 수행해 왔습니다. 시스템 브링업부터 양산 배포까지 전 과정을 책임지는 실전 중심의 솔루션을 제공합니다."

services:
  title: "서비스 (Engineering Services)"
  cards:
    - title: "RTOS & 초저전력 펌웨어 개발"
      body: "Zephyr, FreeRTOS 등 오픈소스 RTOS 기반의 맞춤형 아키텍처 설계; 초소형·저전력 미션 크리티컬 디바이스를 위한 고신뢰성 펌웨어 구현"
    - title: "임베디드 리눅스 & BSP 엔지니어링"
      body: "Yocto Project / Buildroot 기반 커스텀 리눅스 BSP 구축; 디바이스 드라이버 작성, 커널 최적화, 실시간성(PREEMPT_RT) 확보 및 시스템 이식"
    - title: "라이다(LiDAR) 센서 데이터 처리 & 파이프라인"
      body: "3D 라이다 포인트 클라우드(Point Cloud) 실시간 수집 및 필터링; 임베디드 타겟 플랫폼에 최적화된 객체 인식, 점군 데이터 압축 및 3D 공간 파이프라인 구축"
    - title: "임베디드 비전 & 카메라 영상 처리"
      body: "MIPI-CSI / USB / Ethernet 카메라 인터페이스 드라이버 개발; OpenCV 및 Hardware Accelerator(GPU/NPU) 기반 실시간 영상 전처리, 파이프라인 및 Edge AI 최적화"
    - title: "초고속 디바이스 드라이버 & Bus 인터페이스"
      body: "I2C, SPI, UART부터 USB, PCIe, CAN, Ethernet까지; 하드웨어 특성을 극대화하는 레지스터 수준 드라이버 및 통신 아키텍처 설계"
    - title: "시스템 브링업 & 트러블슈팅"
      body: "신규 개발 SoC/FPGA 보드의 하드웨어 초기화 및 OS 임베딩; 오실로스코프 및 로직 분석기 기반의 하드웨어-소프트웨어 통합 디버깅"
    - title: "시큐어 부트(Secure Boot) & 보안 솔루션"
      body: "MCUboot, ARM TrustZone 기반의 안전한 부트로더 설계; 암호화 키 관리, 무결성 검증 및 안전한 FOTA(Firmware Over-The-Air) 구현"
    - title: "초저전력 최적화 & 시스템 프로파일링"
      body: "동적 전력 관리(DVFS) 및 딥 슬립 모드 아키텍처 적용; 런타임 성능 프로파일링을 통한 리소스 소모 최소화 및 병목 현상 해결"
    - title: "임베디드 CI/CD & HIL 테스트 인프라"
      body: "실제 타겟 하드웨어 연동 HIL(Hardware-in-the-Loop) 자동화 파이프라인 구축; 빌드·테스트·배포 전 과정의 자동화로 소프트웨어 품질 확보"
    - title: "로보틱스 & Edge AI 시스템 통합"
      body: "ROS / ROS 2 기반의 분산 로봇 소프트웨어 아키텍처 설계; Edge AI 디바이스 및 AWS IoT 클라우드 파이프라인과의 고성능 데이터 연동"

posts:
  title: "기술 블로그"
  more: "전체 글 보기 &rarr;"

tech:
  title: "기술 스택 (Tech Stack)"
  cards:
    - title: "Languages & OS"
      badges: ["C/C++", "Rust", "Python", "Zephyr RTOS", "FreeRTOS", "Embedded Linux"]
    - title: "Interfaces & Protocols"
      badges: ["I2C / SPI / UART", "USB / PCIe", "CAN / CAN-FD", "Ethernet", "BLE", "WiFi"]
    - title: "Vision, AI & Robotics"
      badges: ["ROS / ROS 2", "LiDAR (Point Cloud)", "OpenCV", "AWS IoT"]
    - title: "Hardware & Tools"
      badges: ["ARM Cortex-M/A", "STM32 / nRF52", "OpenOCD / GDB", "Git / Docker"]

founder:
  title: "설립자"
  name: "정석영 (Seo Jeong)"
  role: "Founder · Principal Engineer"
  badges: ["Amazon", "Qualcomm", "Microsoft", "Samsung Electronics"]
  paragraphs:
    - "정석영 대표는 삼성전자를 시작으로 Amazon, Qualcomm, Microsoft 등 글로벌 빅테크 기업에서 20년 이상 임베디드 소프트웨어 엔지니어로 일하며, 위성 비행 컴퓨터, 드론 제어 시스템, 무선 통신 전력 최적화 등 고신뢰성이 요구되는 핵심 프로젝트들을 성공적으로 수행해 왔습니다."
    - "알펜탈 시스템즈는 이러한 20년의 검증된 현장 경험과 노하우를 바탕으로, 고객사가 믿고 맡길 수 있는 최상의 임베디드 토탈 엔지니어링 솔루션을 제공합니다."

contact:
  title: "문의"
  body: "프로젝트 문의는 이메일로 연락해 주세요."
```

- [ ] **Step 3: Replace `layouts/index.html`**

```html
<!DOCTYPE html>
<html lang="ko">
{{ partial "head.html" . }}
<body>
  {{ partial "header.html" . }}
  {{- $h := index .Site.Data "ko" "home" }}

  <main id="top">
    <section class="hero">
      <div class="container">
        <h1>{{ .Site.Params.tagline }}</h1>
        <p class="hero-sub">{{ $h.hero_sub }}</p>
      </div>
    </section>

    <section id="about" class="section">
      <div class="container">
        <h2>{{ $h.about.title }}</h2>
        <p>{{ $h.about.body }}</p>
      </div>
    </section>

    <section id="services" class="section alt">
      <div class="container">
        <h2>{{ $h.services.title }}</h2>
        <div class="cards">
          {{- range $h.services.cards }}
          <div class="card">
            <h3>{{ .title }}</h3>
            <p>{{ .body }}</p>
          </div>
          {{- end }}
        </div>
      </div>
    </section>

    {{- with first 3 (where .Site.RegularPages "Section" "posts").ByDate.Reverse }}
    <section id="posts" class="section section-bordered">
      <div class="container">
        <h2>{{ $h.posts.title }}</h2>
        {{ partial "post-list.html" . }}
        <p class="more-link"><a href="{{ "/posts/" | relURL }}">{{ $h.posts.more | safeHTML }}</a></p>
      </div>
    </section>
    {{- end }}

    <section id="tech-stack" class="section alt">
      <div class="container">
        <h2>{{ $h.tech.title }}</h2>
        <div class="cards">
          {{- range $h.tech.cards }}
          <div class="card">
            <h3>{{ .title }}</h3>
            <div class="badges">
              {{- range .badges }}
              <span class="badge">{{ . }}</span>
              {{- end }}
            </div>
          </div>
          {{- end }}
        </div>
      </div>
    </section>

    <section id="founder" class="section">
      <div class="container">
        <h2>{{ $h.founder.title }}</h2>
        <div class="founder">
          <h3>{{ $h.founder.name }}</h3>
          <p class="founder-title">{{ $h.founder.role }}</p>
          <ul class="tags founder-badges">
            {{- range $h.founder.badges }}
            <li>{{ . }}</li>
            {{- end }}
          </ul>
          {{- range $h.founder.paragraphs }}
          <p>{{ . }}</p>
          {{- end }}
        </div>
      </div>
    </section>

    <section id="contact" class="section alt">
      <div class="container">
        <h2>{{ $h.contact.title }}</h2>
        <p>{{ $h.contact.body }}</p>
        <a class="cta" href="mailto:{{ .Site.Params.contactEmail }}">{{ .Site.Params.contactEmail }}</a>
      </div>
    </section>
  </main>

  {{ partial "footer.html" . }}
</body>
</html>
```

- [ ] **Step 4: Compare**

Run: `hugo --gc --minify -d /tmp/rc-site-after >/dev/null && cmp /tmp/rc-site-before/index.html /tmp/rc-site-after/index.html && echo IDENTICAL`
Expected: `IDENTICAL`. If not, find the first difference with `diff <(tr '>' '\n' < /tmp/rc-site-before/index.html) <(tr '>' '\n' < /tmp/rc-site-after/index.html) | head` and fix the data or template (not the reference).

- [ ] **Step 5: Commit**

```bash
git add data/ko/home.yaml layouts/index.html
git commit -m "refactor: move landing page copy into a data file" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Languages, UI strings, and the English landing page

**Files:**
- Modify: `hugo.toml`, `layouts/index.html`, `layouts/partials/header.html`, `layouts/partials/footer.html`, `layouts/posts/list.html`, `layouts/posts/single.html`
- Create: `i18n/ko.toml`, `i18n/en.toml`, `data/en/home.yaml`, `layouts/partials/ko-posts.html`

**Interfaces:**
- Produces: `partial "ko-posts.html" .` returns the Korean posts (a page collection) from any language; i18n keys listed below.

- [ ] **Step 1: Reference build**

Run: `hugo --gc --minify -d /tmp/rc-site-before >/dev/null`

- [ ] **Step 2: Config**

In `hugo.toml`, remove the top-level lines `languageCode = "ko-KR"` and `title = "알펜탈 시스템즈 (Alpental Systems)"`, and the line `tagline = "임베디드 시스템을 위한 토탈 엔지니어링 솔루션"` under `[params]`. Add after `enableRobotsTXT = true`:

```toml
defaultContentLanguage = "ko"
defaultContentLanguageInSubdir = false
```

and at the end of the file:

```toml
[languages.ko]
  languageCode = "ko-KR"
  languageName = "한국어"
  weight = 1
  title = "알펜탈 시스템즈 (Alpental Systems)"
  [languages.ko.params]
    tagline = "임베디드 시스템을 위한 토탈 엔지니어링 솔루션"

[languages.en]
  languageCode = "en-US"
  languageName = "English"
  weight = 2
  title = "Alpental Systems"
  [languages.en.params]
    tagline = "End-to-end embedded engineering, from board bring-up to mass production"
```

- [ ] **Step 3: UI strings**

Create `i18n/ko.toml`:

```toml
wordmark = "알펜탈 시스템즈"
nav_about = "소개"
nav_services = "서비스"
nav_blog = "기술 블로그"
nav_tech = "기술 스택"
nav_founder = "설립자"
nav_contact = "문의"
switch_label = "EN"
footer_registration = "대표 JEONG SEOKYOUNG | 사업자등록번호 208-16-07646"
no_posts = "아직 게시된 글이 없습니다."
view_code = "View code on GitHub"
post_contact = "비슷한 프로젝트를 검토 중이시면 연락 주세요."
read_full_ko = "Read the full article (Korean) &rarr;"
read_article = "Read the article &rarr;"
code_on_github = "Code on GitHub"
og_locale = "ko_KR"
```

Create `i18n/en.toml`:

```toml
wordmark = "Alpental Systems"
nav_about = "About"
nav_services = "Services"
nav_blog = "Blog"
nav_tech = "Tech Stack"
nav_founder = "Founder"
nav_contact = "Contact"
switch_label = "한국어"
footer_registration = "Representative: JEONG SEOKYOUNG · Business registration no. 208-16-07646 (Republic of Korea)"
no_posts = "No posts yet."
view_code = "View code on GitHub"
post_contact = "Contact"
read_full_ko = "Read the full article (Korean) &rarr;"
read_article = "Read the article &rarr;"
code_on_github = "Code on GitHub"
og_locale = "en_US"
```

- [ ] **Step 4: Korean posts from any language**

Create `layouts/partials/ko-posts.html`:

```html
{{- /* The Korean posts, from any language: English has no post files of its own. */ -}}
{{- $section := site.GetPage "/posts" }}
{{- $pages := $section.Pages }}
{{- if ne site.Language.Lang "ko" }}
  {{- range $section.Translations }}
    {{- if eq .Language.Lang "ko" }}{{ $pages = .Pages }}{{ end }}
  {{- end }}
{{- end }}
{{- return $pages }}
```

- [ ] **Step 5: English copy**

Create `data/en/home.yaml` with the English copy from the spec's "English copy" section:

```yaml
hero_sub: "Built on two decades of research and mass-production experience at Samsung, Amazon, Microsoft, and Qualcomm."

about:
  title: "About"
  body: "Alpental Systems is an engineering company built on more than 20 years of hands-on work in embedded firmware, RTOS, and device drivers, which its founder gained as a software engineer at Samsung Electronics, Amazon, Microsoft, and Qualcomm. Past projects span aerospace and consumer electronics: satellite flight computer systems, drone battery management systems (BMS), flight termination systems (FTS), WLAN SoC power optimization, Windows device drivers, edge-device data processing with AWS, and mass-production support. We take responsibility for the whole path from system bring-up to production deployment."

services:
  title: "Engineering Services"
  cards:
    - title: "RTOS & Ultra-Low-Power Firmware"
      body: "Custom architectures on open-source RTOSes such as Zephyr and FreeRTOS; high-reliability firmware for small, low-power, mission-critical devices."
    - title: "Embedded Linux & BSP Engineering"
      body: "Custom Linux BSPs with the Yocto Project and Buildroot; device drivers, kernel optimization, real-time performance with PREEMPT_RT, and system porting."
    - title: "LiDAR Sensor Data Processing & Pipelines"
      body: "Real-time 3D LiDAR point cloud capture and filtering; object detection, point cloud compression, and 3D spatial pipelines optimized for embedded targets."
    - title: "Embedded Vision & Camera Processing"
      body: "Camera interface drivers for MIPI-CSI, USB, and Ethernet; real-time image preprocessing and pipelines with OpenCV and GPU/NPU accelerators, optimized for edge AI."
    - title: "High-Speed Device Drivers & Bus Interfaces"
      body: "From I2C, SPI, and UART to USB, PCIe, CAN, and Ethernet: register-level drivers and communication architectures that get the most out of the hardware."
    - title: "System Bring-up & Troubleshooting"
      body: "Hardware initialization and OS porting for new SoC and FPGA boards; hardware-software integration debugging with oscilloscopes and logic analyzers."
    - title: "Secure Boot & Security"
      body: "Secure bootloaders with MCUboot and Arm TrustZone; key management, integrity verification, and secure firmware updates over the air (FOTA)."
    - title: "Low-Power Optimization & System Profiling"
      body: "Dynamic power management (DVFS) and deep-sleep architectures; runtime profiling to cut resource use and remove bottlenecks."
    - title: "Embedded CI/CD & HIL Test Infrastructure"
      body: "Automated hardware-in-the-loop (HIL) pipelines on real target hardware; build, test, and release automation for consistent software quality."
    - title: "Robotics & Edge AI Integration"
      body: "Distributed robot software architectures on ROS and ROS 2; high-performance data paths between edge AI devices and AWS IoT cloud pipelines."

posts:
  title: "Technical Blog"
  more: "All posts &rarr;"

tech:
  title: "Tech Stack"
  cards:
    - title: "Languages & OS"
      badges: ["C/C++", "Rust", "Python", "Zephyr RTOS", "FreeRTOS", "Embedded Linux"]
    - title: "Interfaces & Protocols"
      badges: ["I2C / SPI / UART", "USB / PCIe", "CAN / CAN-FD", "Ethernet", "BLE", "WiFi"]
    - title: "Vision, AI & Robotics"
      badges: ["ROS / ROS 2", "LiDAR (Point Cloud)", "OpenCV", "AWS IoT"]
    - title: "Hardware & Tools"
      badges: ["ARM Cortex-M/A", "STM32 / nRF52", "OpenOCD / GDB", "Git / Docker"]

founder:
  title: "Founder"
  name: "Seo Jeong (정석영)"
  role: "Founder · Principal Engineer"
  badges: ["Amazon", "Qualcomm", "Microsoft", "Samsung Electronics"]
  paragraphs:
    - "Seo Jeong began at Samsung Electronics and has spent more than 20 years as an embedded software engineer at global technology companies including Amazon, Qualcomm, and Microsoft, delivering high-reliability work on satellite flight computers, drone control systems, and wireless power optimization."
    - "Alpental Systems brings this field experience to every engagement and takes responsibility for embedded engineering from start to finish."

contact:
  title: "Contact"
  body: "For project inquiries, please email us."
```

- [ ] **Step 6: Templates**

In `layouts/index.html`:
- change `<html lang="ko">` to `<html lang="{{ .Site.Language.Lang }}">`;
- change `{{- $h := index .Site.Data "ko" "home" }}` to `{{- $h := index .Site.Data .Site.Language.Lang "home" }}`;
- replace the whole `{{- with first 3 ... }}` block (through its `{{- end }}`) with:

```html
    {{- $posts := partial "ko-posts.html" . }}
    {{- with first 3 $posts.ByDate.Reverse }}
    <section id="posts" class="section section-bordered">
      <div class="container">
        <h2>{{ $h.posts.title }}</h2>
        {{- if eq $.Site.Language.Lang "ko" }}
        {{ partial "post-list.html" . }}
        {{- else }}
        {{ partial "post-list-en.html" (dict "pages" . "full" false) }}
        {{- end }}
        <p class="more-link"><a href="{{ "/posts/" | relLangURL }}">{{ $h.posts.more | safeHTML }}</a></p>
      </div>
    </section>
    {{- end }}
```

Replace `layouts/partials/header.html` with:

```html
<header class="site-header">
  <div class="container header-inner">
    <a class="wordmark" href="{{ "/" | relLangURL }}">{{ i18n "wordmark" }}</a>
    <nav class="nav">
      <a href="{{ "/#about" | relLangURL }}">{{ i18n "nav_about" }}</a>
      <a href="{{ "/#services" | relLangURL }}">{{ i18n "nav_services" }}</a>
      {{- if partial "ko-posts.html" . }}
      <a href="{{ "/posts/" | relLangURL }}">{{ i18n "nav_blog" }}</a>
      {{- end }}
      <a href="{{ "/#tech-stack" | relLangURL }}">{{ i18n "nav_tech" }}</a>
      <a href="{{ "/#founder" | relLangURL }}">{{ i18n "nav_founder" }}</a>
      <a href="{{ "/#contact" | relLangURL }}">{{ i18n "nav_contact" }}</a>
    </nav>
  </div>
</header>
```

In `layouts/partials/footer.html`, replace `<p>대표 JEONG SEOKYOUNG | 사업자등록번호 208-16-07646</p>` with `<p>{{ i18n "footer_registration" }}</p>`.

In `layouts/posts/list.html`, replace `<p class="page-sub">아직 게시된 글이 없습니다.</p>` with `<p class="page-sub">{{ i18n "no_posts" }}</p>` and `<html lang="ko">` with `<html lang="{{ .Site.Language.Lang }}">`.

In `layouts/posts/single.html`, replace `<html lang="ko">` with `<html lang="{{ .Site.Language.Lang }}">`, `View code on GitHub` with `{{ i18n "view_code" }}`, and `비슷한 프로젝트를 검토 중이시면 연락 주세요.` with `{{ i18n "post_contact" }}`.

Create a placeholder `layouts/partials/post-list-en.html` so the English home builds (Task 4 fills it):

```html
<ul class="post-list">
  {{- range .pages }}
  <li><a class="post-title" href="{{ .RelPermalink }}" lang="ko">{{ .Title }}</a></li>
  {{- end }}
</ul>
```

- [ ] **Step 7: Check the Korean pages did not change**

Run: `hugo --gc --minify -d /tmp/rc-site-after 2>&1 | grep -E "ERROR|WARN"; for f in index.html posts/index.html posts/2026-09-redundant-controller/index.html; do cmp /tmp/rc-site-before/$f /tmp/rc-site-after/$f && echo "same $f"; done`
Expected: only the `languageCode` deprecation `WARN` (if any), and `same` for all three Korean pages.

- [ ] **Step 8: Check the English home**

Run: `grep -o '<h2>[^<]*</h2>' /tmp/rc-site-after/en/index.html; grep -o 'lang="[a-z]*"' /tmp/rc-site-after/en/index.html | head -1`
Expected: `About`, `Engineering Services`, `Technical Blog`, `Tech Stack`, `Founder`, `Contact`, and `lang="en"`.

- [ ] **Step 9: Commit**

```bash
git add hugo.toml i18n data/en layouts
git commit -m "feat: add the English landing page" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: English blog list

**Files:**
- Create: `content/posts/_index.en.md`
- Modify: `layouts/partials/post-list-en.html`, `layouts/posts/list.html`, `static/css/style.css`

- [ ] **Step 1: Section page**

Create `content/posts/_index.en.md`:

```markdown
---
title: "Technical Blog"
description: "Engineering notes from Alpental Systems projects. The articles are written in Korean; each entry has an English summary and a link to the code."
---
```

- [ ] **Step 2: List entries**

Replace `layouts/partials/post-list-en.html` with:

```html
{{- /* English entries for Korean posts: .pages, .full (whole summary or a short one). */ -}}
<ul class="post-list">
  {{- range .pages }}
  {{- $target := .RelPermalink }}
  {{- $translated := false }}
  {{- range .Translations }}
    {{- if eq .Language.Lang "en" }}{{ $target = .RelPermalink }}{{ $translated = true }}{{ end }}
  {{- end }}
  <li id="{{ .File.ContentBaseName }}">
    <a class="post-title" href="{{ $target }}"{{ if not $translated }} lang="ko"{{ end }}>{{ .Title }}</a>
    {{- with .Params.summary_en }}
    <p class="post-summary-en">{{ if $.full }}{{ . }}{{ else }}{{ . | plainify | truncate 160 }}{{ end }}</p>
    {{- end }}
    <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "2006-01-02" }}</time>
    {{- if $.full }}
    <p class="post-links">
      <a href="{{ $target }}">{{ if $translated }}{{ i18n "read_article" | safeHTML }}{{ else }}{{ i18n "read_full_ko" | safeHTML }}{{ end }}</a>
      {{- with .Params.repo }} · <a href="{{ . }}">{{ i18n "code_on_github" }}</a>{{ end }}
    </p>
    {{- end }}
  </li>
  {{- end }}
</ul>
```

- [ ] **Step 3: Use it on the English list page**

In `layouts/posts/list.html`, replace

```html
      {{- with .Pages.ByDate.Reverse }}
      {{ partial "post-list.html" . }}
```

with

```html
      {{- $pages := (partial "ko-posts.html" .).ByDate.Reverse }}
      {{- with $pages }}
      {{- if eq $.Site.Language.Lang "ko" }}
      {{ partial "post-list.html" . }}
      {{- else }}
      {{ partial "post-list-en.html" (dict "pages" . "full" true) }}
      {{- end }}
```

Append to `static/css/style.css`:

```css
.post-links {
  margin: 4px 0 0;
  font-size: 0.9rem;
}
```

- [ ] **Step 4: Check**

Run: `hugo --gc --minify -d /tmp/rc-site-after 2>&1 | grep ERROR; cmp /tmp/rc-site-before/posts/index.html /tmp/rc-site-after/posts/index.html && echo "ko list same"; grep -o 'id="2026-09[a-z0-9-]*"' /tmp/rc-site-after/en/posts/index.html; grep -c 'Read the full article' /tmp/rc-site-after/en/posts/index.html`
Expected: `ko list same` (the Korean reference is the Task 3 build, so rebuild it first if needed: `git stash; hugo --gc --minify -d /tmp/rc-site-before; git stash pop`), four `id="2026-09-..."` anchors, and `4`.

- [ ] **Step 5: Commit**

```bash
git add content/posts/_index.en.md layouts static/css/style.css
git commit -m "feat: add the English blog list" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Language switch and search engine tags

**Files:**
- Create: `layouts/partials/lang-switch.html`
- Modify: `layouts/partials/header.html`, `layouts/partials/head.html`

- [ ] **Step 1: Switch**

Create `layouts/partials/lang-switch.html`:

```html
{{- /* Link to this page in the other language; a Korean post without a translation goes to its English list entry. */ -}}
{{- $target := "" }}
{{- $lang := "" }}
{{- range .Translations }}{{ $target = .RelPermalink }}{{ $lang = .Language.Lang }}{{ end }}
{{- if not $target }}
  {{- range site.Home.Translations }}
    {{- $target = .RelPermalink }}
    {{- $lang = .Language.Lang }}
    {{- if and $.IsPage (eq $.Section "posts") (eq $.Site.Language.Lang "ko") }}
      {{- $target = printf "%sposts/#%s" .RelPermalink $.File.ContentBaseName }}
    {{- end }}
  {{- end }}
{{- end }}
{{- with $target }}
<a class="lang-switch" href="{{ . }}" hreflang="{{ $lang }}">{{ i18n "switch_label" }}</a>
{{- end }}
```

In `layouts/partials/header.html`, add before `</nav>`:

```html
      {{ partial "lang-switch.html" . }}
```

- [ ] **Step 2: Head tags**

In `layouts/partials/head.html`, add after the `og:url` line:

```html
  <meta property="og:locale" content="{{ i18n "og_locale" }}">
  {{- if .IsTranslated }}
  {{- range .AllTranslations }}
  <link rel="alternate" hreflang="{{ .Language.Lang }}" href="{{ .Permalink }}">
  {{- if eq .Language.Lang "en" }}
  <link rel="alternate" hreflang="x-default" href="{{ .Permalink }}">
  {{- end }}
  {{- end }}
  {{- end }}
```

- [ ] **Step 3: Check the switch targets and links**

Run:
```bash
hugo --gc --minify -d /tmp/rc-site-after 2>&1 | grep ERROR
for f in index.html en/index.html posts/index.html en/posts/index.html posts/2026-09-redundant-controller/index.html; do
  echo "$f -> $(grep -o 'class=lang-switch href=[^ >]*\|class="lang-switch" href="[^"]*"' /tmp/rc-site-after/$f)"; done
grep -o 'hreflang=[^ ]* href=[^ >]*' /tmp/rc-site-after/index.html
python3 scripts/check-links.py /tmp/rc-site-after https://alpentalsystems.com/
```
Expected: the Korean home switches to `/en/`, the English home to `/`, the Korean list to `/en/posts/`, the English list to `/posts/`, the Korean post to `/en/posts/#2026-09-redundant-controller`; the Korean home has `hreflang` `ko`, `en`, and `x-default`; the link check reports `0 broken`.

- [ ] **Step 4: Commit**

```bash
git add layouts
git commit -m "feat: add a language switch and hreflang tags" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Preview and owner review

- [ ] **Step 1: Preview**

Run `hugo server` (without `-D`) and ask the owner to check at desktop and phone width: `/`, `/en/`, `/posts/`, `/en/posts/`, one Korean post, the language switch on each, and the English wording.

- [ ] **Step 2: Publish only on the owner's word**

After approval: merge `feat/bilingual` into `main` and push. Then ask the owner to check the Cloudflare Pages build log (the Hugo version there is not known to this repo), and to register `https://alpentalsystems.com/sitemap.xml` with Naver Search Advisor (searchadvisor.naver.com, 사이트 등록 then 요청 > 사이트맵 제출) and Google Search Console (Sitemaps).
