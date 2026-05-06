---
name: blog-index
description: Fetch all [Playlist] posts from a Naver blog and save to data/playlist_index.json. Use when you want to initialize or refresh the playlist index file for bulk dataset building.
argument-hint: [blog_id]
arguments: [blog_id]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read Write
---

## 목적

네이버 블로그에서 `[Playlist]` 접두사 글을 전부 가져와 `data/playlist_index.json`에 저장한다.
기존 파일이 있으면 새 글만 추가하고 기존 status는 보존한다.

## 입력

- `$0` (`blog_id`): 네이버 블로그 아이디, 예: `janjanjae`

## 출력

`data/playlist_index.json` 생성/업데이트. 각 항목 형식:
```json
{
  "playlist_key": "26_Apr_1st",
  "blog_url": "https://blog.naver.com/janjanjae/224274206483",
  "title": "26_Apr_1st 망설임은 항상 내 편",
  "date": "2026. 5. 4.",
  "log_no": "224274206483",
  "status": "pending"
}
```

`status` 값: `pending` | `built` | `mismatch` | `skip` | `error`

## 실행 절차

1. 아래 명령을 실행한다:

```bash
uv run python -m src.ingest.blog_index "$0" --save
```

2. `data/playlist_index.json` 열어서 확인:
   - `playlist_key`가 빈 항목 → 수동으로 키 입력하거나 `"status": "skip"` 처리
   - 두 달 합친 글 등 특이 케이스 확인

3. 정리 완료 후 `/dataset-build-all`로 일괄 빌드

## 실패 처리

- 네트워크 오류: ZTNA/VPN 상태 확인
- `playlist_key` 빈 항목: `playlist_index.json`에서 직접 값 입력
