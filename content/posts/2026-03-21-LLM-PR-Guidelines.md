---
title: LLM PR Guidelines
date: 2026-03-21
description: GitHub repo의 LLM을 이용한 PR에 대한 Gudelines의 유용성
categories:
  - Coding
tags:
  - LLM
  - AI
draft: false
---
지난 몇일 동안 Claude Code를 사용해서 GitHub PR들을 만들어 왔는데, 그 중 두 개:

* [cpu/native/makefiles: add 'make coverage' target for native board](https://github.com/RIOT-OS/RIOT/pull/22148)
* [docs : fix Metal backend op support status in ops.md](https://github.com/ggml-org/llama.cpp/pull/20779)

각각 RIOT와  Zyphyr embedded OS repo에 만든 것인데 두 커뮤너티 다 AI를 사용한 PR에 대한 disclosure를 해야한다는 가이드가 있다. RIOT 커뮤의 경우 좀 더 자세히 언급하게 되어 있다.([#22004](https://github.com/RIOT-OS/RIOT/pull/22004)) 

PR 리뷰어의 입장에서는 이 PR을 어느 정도 신뢰할 수 있을지 가늠하는 것이 필요할 것  이다. AI에게 맡겨 버리고 결과를 이해하지 못한 채 만든 PR은 어느 정도 리스크가 있으니까. 

두 주 정도 Claude Code Pro 플랜을 결제해서 사용해  본 내 경험은. Claude는 놀랄 정도로 정확하는 것. 코드 네비게이션, 구조, 파악 후 unit test crash를 찾을 때 링크된 function address를 찾아가는 정도이다. 사용되는 툴들이 어떻게 동작하는지 정확히 이해하고 있다.

문제가 생기면 책임 지는 것은 사람이니까 사람이 gate keeper 노릇을 하는 것이 _현재로는_ 합리적이지만, 이미 AI가 문제를 해결하는 능력이 사람을 추월해 버렸다.

전통적인 의미의 software developer, programmer, software development engineer가 사라질 것이라 하는 예상이 밎을지 늦어도 올 해 말이면 알 수 있을 듯.