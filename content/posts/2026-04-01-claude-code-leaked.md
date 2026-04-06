---
title: Claude code .map 파일이 유출됨
date: 2026-04-01T03:30:00+08:00
description: Antrophic의 Claude code 일부 소스 코드가 유출됨
categories:
  - Coding
tags:
  - Claude
draft: false
---
아마 한국 시간 3/31일 밤일 듯 한데, [Anthropic의 Claude Code version 2.1.88 릴리즈에 59.8MB의 JS source map file이 포함되어 배포 되는 사고](https://www.theregister.com/2026/03/31/anthropic_claude_code_source_code/)(의도했을리는 없으므로 사고로 봐야)가 발생했다.

`.map` 파일은 빌드된 결과물을 원본 소스코드와 `map`하기 위한 정보를 담고 있다. 개발자가 디버깅을 할 때 필요한 정보이고, 일반적으로 정식 릴리즈에는 포함되지 않는 파일이다.

```json
{
  "version": 3,
  "sources": ["src/main.ts", "src/tools/bash.ts", "src/query.ts"],
  "sourcesContent": ["...full original source of main.ts...",
                     "...full original source of bash.ts...",
                     "..."],
  "mappings": "AAAA,SAAS,CAAC..."
}
```

여기서 `sourcesContent` 필드에 원본 소스 코드가 들어 있어 문제가 된 것이다.

Anthropic은 대응은 쿨 하다.

> "Earlier today, a Claude Code release included some internal source code. No sensitive customer data or credentials were involved or exposed. This was a release packaging issue caused by human error, not a security breach. We're rolling out measures to prevent this from happening again."

유출된 소스 코드를 다시 Claude Code에 먹여서 이런 저런 결과들이 나오고 있는데 내 레이더에 잡힌 몇 개.

* [Claude Code documentation](https://www.mintlify.com/VineeTagarwaL-code/claude-code) - 내부에서 어떻게 동작하는지 살짝 들여다 볼 수 있다.
* [Claw Code](https://github.com/instructkr/claw-code) - Claude Code의 Python / Rust 클론
* [Open Claude](https://github.com/Gitlawb/openclaude) - 유출된 Claude Code를 fork해서 다른 LLM을 쓸 수 있게 함
