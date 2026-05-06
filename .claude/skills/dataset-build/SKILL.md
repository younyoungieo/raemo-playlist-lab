---
name: dataset-build
description: Run the full raemo dataset pipeline: fetch YouTube playlist, fetch Naver blog, clean lines, position-join, and save JSON. Use when you want to build or rebuild a playlist dataset from scratch. YouTube URL is auto-extracted from the blog post if not provided.
argument-hint: [playlist_key] [blog_url] [youtube_url?]
arguments: [playlist_key, blog_url, youtube_url]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read Write
---

## 목적

YouTube 플레이리스트 + 네이버 블로그 → position join → `data/datasets/{playlist_key}.json` 생성.
YouTube URL은 블로그 본문에서 자동 추출되므로 생략 가능.

## 입력

- `$0` (`playlist_key`): 데이터셋 식별자, 예: `26_Apr_1st`
- `$1` (`blog_url`): 네이버 블로그 포스트 URL
- `$2` (`youtube_url`): YouTube URL (선택 — 생략 시 블로그에서 자동 추출)

## 출력

- `data/datasets/{playlist_key}.json` — Dataset JSON (스키마: CLAUDE.md 참고)
- 콘솔에 Validation 결과 출력

## 실행 절차

블로그 URL만으로 실행 (YouTube URL 자동 추출):
```bash
uv run python -m src.dataset.builder "$0" "$1"
```

YouTube URL을 직접 지정:
```bash
uv run python -m src.dataset.builder "$0" "$1" "$2"
```

강제 갱신 (캐시 무시):
```bash
uv run python -m src.dataset.builder "$0" "$1" --force-refresh
```

2. Validation status 확인:
   - `OK` → 완료
   - `MISMATCH` → `/dataset-validate $0` 로 diff 리포트 확인 후 원인 파악

## 실패 처리

- `No YouTube playlist URL found in blog post` → 블로그에 유튜브 링크 없음, `$2`로 직접 전달
- YouTube fetch 실패 → `/youtube-ingest $2` 단독 실행으로 원인 확인
- Blog fetch 실패 → `/blog-extract $1` 단독 실행으로 원인 확인
- Mismatch → `/lines-clean {raw_file}` 로 정제 결과 점검
