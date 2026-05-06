# raemo-playlist-lab

래모(raemo) 유튜브 플레이리스트 채널 자동화 프로젝트.

## 핵심 가정

- 네이버 블로그 n번째 줄 = YouTube 플레이리스트 n번째 곡 (position join)
- Phase 1: 메타데이터만 (오디오/영상 다운로드 없음)

## 프로젝트 구조

```
src/ingest/    youtube.py, blog.py
src/clean/     lines.py (규칙 기반 정제)
src/dataset/   schema.py (Pydantic v2), builder.py, validate.py
data/raw/      캐시 (git 추적 안 함)
data/datasets/ 최종 JSON 출력
.claude/skills/ Claude Code Skills (5개)
```

## 환경 설정

```bash
uv sync
cp .env.example .env  # 필요 시 API 키 설정
```

## 주요 명령어 (Skills)

```
/youtube-ingest [playlist_url]    # YT 트랙 목록 추출
/blog-extract   [blog_url]        # Naver 블로그 본문 추출
/lines-clean    [raw_file_path]   # 가사 라인 정제
/dataset-build  [key] [yt_url] [blog_url]  # 전체 파이프라인
/dataset-validate [playlist_key]  # 검증 + diff 리포트
```

## 기술 스택

- Python 3.12 + uv
- yt-dlp (YouTube), requests + BS4 (Naver blog)
- Pydantic v2 (스키마), regex (유니코드 패턴)
- python-dotenv (.env 관리)

## 출력 스키마 (`data/datasets/{playlist_key}.json`)

```json
{
  "playlist_key": "26_Mar_1st",
  "source": { "playlist_id": "...", "blog_post_url": "..." },
  "tracks": [
    {
      "position": 1,
      "youtube_video_id": "...",
      "youtube_title": "...",
      "youtube_channel": "...",
      "lyric_line": "..."
    }
  ],
  "validation": {
    "youtube_count": 0,
    "lyric_line_count": 0,
    "joined_count": 0,
    "status": "ok|mismatch",
    "notes": "..."
  }
}
```

## 캐시 규칙

| 경로 | 캐시 키 | 갱신 |
|------|---------|------|
| `data/raw/youtube/{playlist_id}.json` | playlist_id | `--force-refresh` |
| `data/raw/blog/{md5(url)}.txt` | URL MD5 | `--force-refresh` |
| `data/raw/llm/{md5(input)}.json` | 입력 MD5 | `--force-refresh` |

## 블로그 정제 규칙

```
[REMOVE] 빈 줄
[REMOVE] 이모지 시작 줄 (제목)
[REMOVE] 구분선 (---, •••, ..., 등)
[REMOVE] 이탤릭 코멘트 (*text*)
[STRIP PREFIX] 번호 prefix (1. → 내용만)
[REMOVE] 정제 후 5자 미만
[KEEP] 나머지 → 가사 한 줄
```
