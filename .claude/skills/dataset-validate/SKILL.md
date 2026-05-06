---
name: dataset-validate
description: Validate an existing raemo playlist dataset and print a diff report. Use after building a dataset to check for count mismatches between YouTube tracks and blog lyric lines.
argument-hint: [playlist_key]
arguments: [playlist_key]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read
---

## 목적

`data/datasets/{playlist_key}.json`을 읽어 YouTube 트랙 수 vs 블로그 가사 라인 수를 비교하고 불일치 위치를 리포트한다.

## 입력

- `$0` (`playlist_key`): 검증할 데이터셋 키, 예: `26_Mar_1st`

## 출력

콘솔에 Validation Report 출력:
- 트랙 수 / 가사 줄 수 / Joined 수
- Status: `OK` or `MISMATCH`
- Mismatch 시: 불일치 position 목록

## 실행 절차

1. 아래 명령을 실행한다:

```bash
uv run python -m src.dataset.validate "$0"
```

2. MISMATCH 원인 분석:
   - YouTube 쪽 여분 → 비공개/삭제 영상이 yt-dlp에서 누락됐을 가능성
   - Blog 쪽 여분 → 정제 규칙이 충분하지 않아 비가사 줄이 남아 있는 경우
   
3. 수정 후 `/dataset-build $0 ... --force-refresh`로 재빌드

## 실패 처리

- `Dataset not found`: `data/datasets/$0.json` 없음 → `/dataset-build` 먼저 실행
- JSON 파싱 오류: 파일 손상 → `--force-refresh`로 재빌드
