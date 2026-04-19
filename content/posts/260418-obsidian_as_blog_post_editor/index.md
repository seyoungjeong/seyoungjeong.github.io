---
title: 블로그 포스팅 에디터로 쓰기 위해 Obsidian 설정 하기
date: 2026-04-18T20:57:28+09:00
lastmod: 2026-04-19T20:06:34+09:00
description: Obsidian을 블로그 포스팅을 작성하기 편하게 만들어 보았다. 사용자 인터페이스는 Typora 처럼 간결하게 만들어서 글쓰기에 집중할 수 있도록 했다.
categories: []
tags:
  - 블로깅
draft: false
---
맥에는 [Typora](https://typora.io/)라는 세련된 에디터가 있다. 글 쓰는데 집중할 수 있도록 간결한 사용자 인터페이스를 제공한다. Vim으로는 코딩을, Obsidian으로는 기술 문서를 작성해야 할 것 같은데, Typora를 띄우면 *그 와는 다른 종류의 글로 화면을 채울 수 있을 것 같은*  분위기가 만들어 진다. $10을 써서 사볼까 잠깐 생각했다가 Obsidian 설정을 조금 손 봐서 비슷하게 만들어 보았다. 

![](Screenshot%202026-04-18%20at%208.59.09%20PM.png)
Minimal theme과 Minimal theme settings를 설치해서 focus mode를 on한다. 그러면 거추장 스러운 타이틀바나 상태바들이 사라진다.

다음 헤더의 `date`와 `lastmod` 필드를 자동으로 업데이트 하기 위해서 Update modified date 플러그인을 설치했다. 헤더는 새 포스트를 만들 때 템플릿으로 생성된다.

.obsidian 폴더에 저장되는 설정 파일들은 블로그 repo에 같이 저장해 놓았다.