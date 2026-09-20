# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Personal blog at https://seyoungjeong.github.io/, built with Hugo + PaperMod theme and deployed to GitHub Pages by `.github/workflows/hugo.yaml` (Hugo `0.146.0`, extended). Site language is `ko-KR`; most post bodies are in Korean.

## Common commands

- `hugo server -D` — local preview including drafts (`draft: true`).
- `hugo server` — local preview as published (drafts hidden).
- `hugo --gc --minify` — production build into `public/` (same flags CI uses).
- `hugo new posts/YYYY-MM-DD-slug.md` — create a post from `archetypes/default.md`. The Obsidian flow (see below) is the usual path; the archetype exists as a fallback.
- `git submodule update --init --recursive` — required after a fresh clone; `themes/PaperMod` is a submodule pinned in `.gitmodules`.

There is no lint or test suite; `scripts/` is empty. Do not invent commands.

## Architecture big picture

- **Hugo site config** lives in `config.toml`. Notable bits: `relativeURLs = true`, home outputs include `JSON` (for PaperMod search), menu entries for RSS / Search / Tags / About.
- **Theme is vendored as a submodule** at `themes/PaperMod`. Do not edit files under `themes/`; override by mirroring the path under the repo's own `layouts/` (Hugo's lookup order picks the project copy first).
- **Local layout overrides** that shape the site's visible behavior:
  - `layouts/index.html` — custom home page. Groups `site.RegularPages` by `"January, 2006"` into a monthly archive rather than PaperMod's default list. Respects `site.Params.mainSections` and skips posts with `hiddenInHomeList: true`.
  - `layouts/_default/single.html` and `list.html` — custom header meta (date + tag pills) and draft badge SVG.
  - `layouts/partials/extend_head.html` — loads Pretendard webfont, Google Analytics (`G-QCSTM1SMXR`), and the Google site verification meta tag. This is the hook point for head-tag additions.
  - `layouts/shortcodes/drawio.html` — `{{< drawio "/diagrams/foo.drawio" >}}` renders a diagrams.net viewer; `viewer-static.min.js` is loaded once per page via a window flag.
- **Assets**: images in `static/images/`, drawio sources in `static/diagrams/`, custom CSS in `assets/css/`. Fonts (JetBrains Mono, NeoDGM) are served locally from `static/fonts/` and referenced from `custom.css` (see the comment in `extend_head.html`).

## Authoring flow (Obsidian-driven)

The repo root doubles as an Obsidian vault. `.obsidian/app.json` is set up so that:

- New notes are created in `content/posts/` (`newFileFolderPath`).
- Attachments (pasted/dragged images) go to `static/images/` (`attachmentFolderPath`).
- The `frontmatter-modified-date` plugin auto-maintains the `lastmod` field in `YYYY-MM-DDTHH:mm:ssZ` format; the `date` field is treated as the created-date property. Do not hand-edit `lastmod` to match `date` — let the plugin manage it.
- Templates live in `content/_templates/` (`post-template.md` is the canonical front matter skeleton). `content/_templates/` is not a Hugo section; Hugo ignores leading-underscore directories.

Post filename convention is `YYYY-MM-DD-slug.md` under `content/posts/`. Front matter is **YAML** (`---` fenced) in posts even though `config.toml` uses TOML; match the existing posts rather than the TOML form produced by `hugo new`. Required/expected keys: `title`, `date`, `lastmod`, `description`, `categories`, `tags`, `draft`.

Obsidian wikilink image syntax (`![[file.png]]`) appears in some drafts. Hugo does not render wikilinks natively — convert to standard markdown (`![alt](/images/file.png)`) before publishing, or the image will not appear on the built site.

## Draft and publish semantics

- `draft: true` posts are excluded from production builds (CI runs `hugo` without `-D`). Flip to `false` to publish.
- The home page filters on `site.Params.mainSections` (defaults to the largest section, i.e. `posts`) and additionally hides anything with `hiddenInHomeList: true` — useful for pages that should exist but not appear in the monthly archive.

## Deploy

Push to `main` triggers `.github/workflows/hugo.yaml`: it checks out with submodules, installs Hugo extended + Dart Sass, builds with `--gc --minify` and the Pages base URL, then uploads `./public` as the Pages artifact. There is no preview environment — merged `main` is production.

## Conventions worth preserving

- Keep `themes/PaperMod` untouched; override via `layouts/` at the repo root.
- When adding head-tag content (analytics, verification, fonts), extend `layouts/partials/extend_head.html` rather than replacing `head.html`.
- The `.claude/worktrees/` subtrees are scratch copies from Claude Code worktree sessions; `.gitignore` excludes `.claude/`. Do not commit anything from there.
