# Alpental Systems tech blog section — design

## Context

`alpentalsystems.com` is a single themeless Hugo landing page (`layouts/index.html`,
`layouts/partials/head.html`, `static/css/style.css`), built by Cloudflare Pages
with `hugo`. There is no `content/` directory and taxonomies are disabled.

The owner will publish technical write-ups of demo projects (first one: a
tilt-compensated compass on STM32F3 Discovery with Zephyr, code in the private
repo `alpentalsystems/stm32f3-zephyr-compass`). The purpose is sales: each post
is proof of the services listed on the landing page.

## Goals

- Add a `/posts/` section to the existing site, reusing its look.
- Full posts in Korean; each post carries a short English summary so US clients
  can understand it.
- Make posts visible from the landing page (nav link + recent-posts section).
- Ship a draft skeleton for the compass post.

## Non-goals

- No Hugo multilingual mode, no separate English pages.
- No tags, categories, or taxonomy pages (`disableKinds` stays as is).
- No comments, search, pagination, or theme.
- No changes to existing landing page copy.

## Content model

- Page bundle per post: `content/posts/<YYYY-MM>-<slug>/index.md`, images in the
  same folder, referenced by relative path (`![alt](scope-i2c.png)`).
- URL: `/posts/<folder-name>/`.
- YAML front matter:

  ```yaml
  title: "..."          # Korean title
  date: 2026-10-05
  description: "..."    # one-line Korean summary; used for meta description
  summary_en: |         # 3-5 English sentences; required for published posts
    ...
  repo: ""              # optional URL; empty while the repo is private
  draft: true
  ```

## Templates

1. Structural (no visible change): extract header and footer from
   `layouts/index.html` into `layouts/partials/header.html` and
   `layouts/partials/footer.html`. Nav anchors become `/#about` style
   (via `relURL`) so they work from any page; the wordmark links to `/`.
2. `layouts/posts/list.html`: section page, newest first. Each item: Korean
   title (link), `summary_en` first line as an English subtitle, date.
3. `layouts/posts/single.html`: title, date, a "Summary (English)" box with
   `summary_en`, Korean body, then a "View code" link when `repo` is set, and a
   contact call-to-action (`mailto:` from `params.contactEmail`).
4. `layouts/partials/head.html`: per-page `<title>` (`Page title | Site title`
   for non-home pages) and description (`description`, falling back to site
   tagline). Add Open Graph tags: `og:title`, `og:description`, `og:type`
   (`article` for posts, `website` otherwise), `og:url`.
5. `layouts/index.html`:
   - Nav: add "기술 블로그" linking to `/posts/`, between 기술 스택 and 문의.
   - New section `#posts` "기술 블로그" after 서비스: the 3 newest published
     posts (title, English subtitle, date) and a link to `/posts/`. The whole
     section renders only when at least one published post exists.

## Styling

Additions to `static/css/style.css`, using existing color variables:
post list items, post body typography (readable line length, headings, lists,
tables, images at max-width 100%), `pre`/`code` blocks, and the English summary
box (`--color-bg-alt` background, accent left border). Code highlighting uses
Hugo's default Chroma output with inline styles; no extra stylesheet.

## Draft post

`content/posts/2026-10-stm32f3-zephyr-compass/index.md`, `draft: true`, with
section headings from the holiday plan: board revision and sensors, environment
setup, reading sensors, compass math and tilt compensation, hard-iron
calibration (before/after), bus waveforms, results and next steps. Body text
left for the owner to write.

## Verification

No test suite exists. Checks after each change:

- `hugo --gc --minify` completes with no errors or warnings.
- Grep the built `public/` output:
  - after step 1, `public/index.html` content is unchanged apart from nav hrefs;
  - `/posts/index.html` exists; the draft post is absent in the production
    build and present with `-D`;
  - the summary box, `og:` tags, and nav link appear where expected;
  - the home `#posts` section is absent when no post is published.
- Owner does a visual check with `hugo server -D`.

## Commits

1. `refactor: extract header and footer partials`
2. `feat: add posts section with list and single layouts` (templates 2-4, styling)
3. `feat: link posts from home page nav and recent posts section`
4. `content: add draft for STM32F3 Zephyr compass post`

This spec and the implementation plan are committed separately as `docs:`
commits before step 1.

Nothing is pushed until the owner reviews.
