# Alpental Systems site: English section — design

Status: draft for owner review, 2026-09-28.

## Context

`alpentalsystems.com` is a themeless Hugo site: a landing page
(`layouts/index.html` with its copy written in the template), a blog
(`layouts/posts/list.html`, `layouts/posts/single.html`), and partials for
head, header, footer, and the post list. Every post has a Korean body and an
English `summary_en` in its front matter. Most clients are Korean; visitors
from GitHub and LinkedIn often read English.

The 2026-09-25 blog design ruled out multilingual mode ("no separate English
pages"). This design replaces that non-goal.

## Goals

- Korean stays the main site at `/`; every existing URL keeps working.
- An English section at `/en/`: the full landing page in English and a blog
  list with each post's English summary.
- A language switch on every page that goes to the page's counterpart.
- Search engines see which pages are counterparts (`hreflang`).
- No extra work per post: the English blog list is built from `summary_en`.

## Non-goals

- No English page per post unless the post has a full English translation.
- No translation of post bodies now (possible later, one post at a time).
- No change to the Korean landing page's visible content or layout.
- No new theme, search, comments, or taxonomies.

## Structure

- Hugo multilingual mode: `ko` (default, served at `/`, weight 1) and `en`
  (served at `/en/`, weight 2). `defaultContentLanguageInSubdir = false`.
- Per-language site title and tagline: `[languages.ko]` keeps today's
  values; `[languages.en]` has `title = "Alpental Systems"` and the English
  tagline below.
- Landing page copy moves from `layouts/index.html` into
  `data/ko/home.yaml` and `data/en/home.yaml`; the template selects the file
  by `.Site.Language.Lang` and loops over sections, cards, and badges. The
  Korean output must stay byte-for-byte the same (see Verification).
- UI strings (menu, footer, post list and post footer labels) live in
  `i18n/ko.toml` and `i18n/en.toml`.
- `content/posts/_index.md` stays Korean; `content/posts/_index.en.md` adds
  the English list page.

| Page | Korean | English |
|---|---|---|
| Home | `/` | `/en/` |
| Blog list | `/posts/` | `/en/posts/` |
| Post | `/posts/<slug>/` | `/en/posts/<slug>/` only if `index.en.md` exists |

## English blog list

`/en/posts/` lists every Korean post, newest first. Each entry has:

- an anchor `id="<slug>"` (the post's directory name),
- the Korean title with the English summary in full (not truncated),
- the date,
- "Read the full article (Korean) →" linking to the Korean post, or to the
  English translation when `index.en.md` exists,
- "Code on GitHub" when the post has `repo`.

The list reads the Korean pages from the default-language site. Intro text
under the title: "Engineering notes from Alpental Systems projects. The
articles are written in Korean; each entry has an English summary and a link
to the code."

## Language switch

The last menu item. On Korean pages it reads "EN"; on English pages it reads
"한국어".

| Current page | Target |
|---|---|
| Home | the other language's home |
| Blog list | the other language's blog list |
| Korean post with a translation | the translation |
| Korean post without a translation | `/en/posts/#<slug>` |
| English post (translation) | the Korean post |

## Head and search engines

- `<html lang="ko">` or `<html lang="en">` from the page language.
- `og:locale` `ko_KR` or `en_US`.
- For pages with a counterpart: `<link rel="alternate" hreflang="ko">`,
  `hreflang="en"`, and `hreflang="x-default"` pointing to the English
  version.
- Hugo's multilingual sitemap index (`/sitemap.xml`) with one sitemap per
  language; `robots.txt` keeps pointing at `/sitemap.xml`.
- The owner registers the site with Naver Search Advisor and Google Search
  Console (manual steps, listed in the plan).

## Footer

- Korean: unchanged.
- English: "© 2026 Alpental Systems. All rights reserved." and
  "Representative: JEONG SEOKYOUNG · Business registration no. 208-16-07646
  (Republic of Korea)".
- Post footer: Korean posts keep "비슷한 프로젝트를 검토 중이시면 연락 주세요."
  and the email; English translated posts show "Contact" and the email.

## English copy

Tone: plain and factual, no superlatives. Technical terms stay as they are.

**Tagline (hero title):** End-to-end embedded engineering, from board
bring-up to mass production

**Hero subtitle:** Built on two decades of research and mass-production
experience at Samsung, Amazon, Microsoft, and Qualcomm.

**About:** Alpental Systems is an engineering company built on more than 20
years of hands-on work in embedded firmware, RTOS, and device drivers, which
its founder gained as a software engineer at Samsung Electronics, Amazon,
Microsoft, and Qualcomm. Past projects span aerospace and consumer
electronics: satellite flight computer systems, drone battery management
systems (BMS), flight termination systems (FTS), WLAN SoC power
optimization, Windows device drivers, edge-device data processing with AWS,
and mass-production support. We take responsibility for the whole path from
system bring-up to production deployment.

**Services (Engineering Services):**

1. **RTOS & Ultra-Low-Power Firmware** — Custom architectures on
   open-source RTOSes such as Zephyr and FreeRTOS; high-reliability firmware
   for small, low-power, mission-critical devices.
2. **Embedded Linux & BSP Engineering** — Custom Linux BSPs with the Yocto
   Project and Buildroot; device drivers, kernel optimization, real-time
   performance with PREEMPT_RT, and system porting.
3. **LiDAR Sensor Data Processing & Pipelines** — Real-time 3D LiDAR point
   cloud capture and filtering; object detection, point cloud compression,
   and 3D spatial pipelines optimized for embedded targets.
4. **Embedded Vision & Camera Processing** — Camera interface drivers for
   MIPI-CSI, USB, and Ethernet; real-time image preprocessing and pipelines
   with OpenCV and GPU/NPU accelerators, optimized for edge AI.
5. **High-Speed Device Drivers & Bus Interfaces** — From I2C, SPI, and UART
   to USB, PCIe, CAN, and Ethernet: register-level drivers and communication
   architectures that get the most out of the hardware.
6. **System Bring-up & Troubleshooting** — Hardware initialization and OS
   porting for new SoC and FPGA boards; hardware-software integration
   debugging with oscilloscopes and logic analyzers.
7. **Secure Boot & Security** — Secure bootloaders with MCUboot and Arm
   TrustZone; key management, integrity verification, and secure firmware
   updates over the air (FOTA).
8. **Low-Power Optimization & System Profiling** — Dynamic power management
   (DVFS) and deep-sleep architectures; runtime profiling to cut resource use
   and remove bottlenecks.
9. **Embedded CI/CD & HIL Test Infrastructure** — Automated
   hardware-in-the-loop (HIL) pipelines on real target hardware; build,
   test, and release automation for consistent software quality.
10. **Robotics & Edge AI Integration** — Distributed robot software
    architectures on ROS and ROS 2; high-performance data paths between edge
    AI devices and AWS IoT cloud pipelines.

**Blog section:** heading "Technical Blog"; link "All posts →".

**Tech Stack:** heading "Tech Stack"; the four card titles and badges are
already in English and stay the same.

**Founder:** heading "Founder"; name "Seo Jeong (정석영)"; title "Founder ·
Principal Engineer"; badges Amazon, Qualcomm, Microsoft, Samsung
Electronics.

> Seo Jeong began at Samsung Electronics and has spent more than 20 years as
> an embedded software engineer at global technology companies including
> Amazon, Qualcomm, and Microsoft, delivering high-reliability work on
> satellite flight computers, drone control systems, and wireless power
> optimization.
>
> Alpental Systems brings this field experience to every engagement and
> takes responsibility for embedded engineering from start to finish.

**Contact:** heading "Contact"; "For project inquiries, please email us.";
the email address.

**Menu:** About · Services · Blog · Tech Stack · Founder · Contact · 한국어

## Verification

There is no test suite; each step is checked on the built site.

1. **Copy move:** build before and after moving the Korean copy into
   `data/ko/home.yaml`; the Korean `index.html` must be identical.
2. **Links:** a script walks the built site (both languages) and checks that
   every internal `href` and every `hreflang` target exists. Any missing
   target fails.
3. **Language switch:** home, blog list, and a post without translation link
   to the targets in the table above.
4. **Visual check** on the local preview: both homes, both blog lists, one
   post, at desktop and phone width.

Work happens on the branch `feat/bilingual`; nothing is pushed until the
owner has seen the preview.
