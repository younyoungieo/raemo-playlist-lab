---
name: blog-extract
description: Fetch and extract raw body text from a public Naver blog post. Use when you need the raw text of the blog side of a raemo playlist (before cleaning). Caches result to data/raw/blog/{hash}.txt.
argument-hint: [naver_blog_url]
arguments: [blog_url]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read
---

## 목적

네이버 블로그 공개 글에서 본문 텍스트를 추출해 `data/raw/blog/{md5hash}.txt`에 캐시한다.

## 입력

- `$blog_url`: 네이버 블로그 포스트 URL  
  예: `https://blog.naver.com/username/12345678`

## 출력

- `data/raw/blog/{16자리_해시}.txt` — 정제 전 본문 텍스트 (줄바꿈 포함)

## 실행 절차

1. 아래 명령을 실행한다:

```bash
uv run python -m src.ingest.blog "$blog_url"
```

강제 갱신이 필요하면:
```bash
uv run python -m src.ingest.blog "$blog_url" --force-refresh
```

2. 출력된 라인 수와 상위 10줄을 확인한다.
3. 예상보다 줄 수가 너무 적거나 많으면 `/lines-clean`으로 정제 후 재확인.

## 실패 처리

- `Empty body extracted`: 로그인 필요 글이거나 JS 렌더링 필요 → URL이 공개 글인지 확인
- `모바일 URL (m.blog.naver.com)`: 자동으로 PC URL로 변환하므로 정상 작동해야 함
- `HTTP 404/403`: URL 오타 또는 삭제된 글
