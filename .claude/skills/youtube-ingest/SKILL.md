---
name: youtube-ingest
description: Extract track list (position, video_id, title, channel) from a YouTube playlist using yt-dlp. Use when you need to fetch or refresh the YouTube side of a raemo playlist dataset. Caches result to data/raw/youtube/{playlist_id}.json.
argument-hint: [youtube_url_or_playlist_id]
arguments: [youtube_url]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read
---

## 목적

YouTube 플레이리스트에서 트랙 목록을 추출해 `data/raw/youtube/{playlist_id}.json`에 캐시한다.

## 입력

- `$youtube_url`: YouTube 플레이리스트 URL 또는 playlist ID  
  예: `https://youtube.com/playlist?list=PLxxxxx` 또는 `PLxxxxx`

## 출력

- `data/raw/youtube/{playlist_id}.json` — TrackMeta 배열
  ```json
  [
    { "position": 1, "video_id": "abc123", "title": "곡 제목", "channel": "채널명" },
    ...
  ]
  ```

## 실행 절차

1. 아래 명령을 실행한다:

```bash
uv run python -m src.ingest.youtube "$youtube_url"
```

강제 갱신이 필요하면:
```bash
uv run python -m src.ingest.youtube "$youtube_url" --force-refresh
```

2. 출력된 트랙 수와 첫 5개 항목을 확인한다.
3. 캐시 파일 경로를 사용자에게 알린다.

## 실패 처리

- `yt-dlp not found`: `uv run pip install yt-dlp` 후 재시도
- `Private playlist` 오류: 플레이리스트가 비공개 → 공개 여부 확인 필요
- `0 tracks found`: URL/ID 오타 확인, 플레이리스트 공개 여부 확인
