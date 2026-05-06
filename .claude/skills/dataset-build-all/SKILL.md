---
name: dataset-build-all
description: Bulk-build datasets for all pending entries in data/playlist_index.json. Use after reviewing and editing the index file. Skips already-built entries.
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read Write
---

## 목적

`data/playlist_index.json`의 `status: pending` 항목을 순서대로 빌드한다.
완료된 항목은 `built`, 실패한 항목은 `error`로 status가 자동 업데이트된다.

## 사전 조건

`data/playlist_index.json`이 존재해야 한다.
없으면 먼저 `/blog-index janjanjae` 실행.

## 실행 절차

dry-run으로 먼저 확인:
```bash
uv run python -m src.dataset.bulk_build --dry-run
```

실제 빌드:
```bash
uv run python -m src.dataset.bulk_build
```

강제 갱신 (캐시 무시):
```bash
uv run python -m src.dataset.bulk_build --force-refresh
```

## 결과 해석

- `✓ OK` → 정상 빌드 완료
- `⚠ MISMATCH` → YouTube 트랙 수 ≠ 블로그 가사 수. `/dataset-validate [key]`로 상세 확인
- `✗ 실패` → YouTube URL 없음, 네트워크 오류 등. error 메시지 확인

## 실패 처리

- `playlist_key 없음`: `playlist_index.json`에서 해당 항목에 키 직접 입력
- MISMATCH: `/dataset-validate [key]` 로 확인 → `data/overrides/[key].json`으로 보정
- 전체 재실행 필요 시: status를 `pending`으로 되돌리고 재실행
