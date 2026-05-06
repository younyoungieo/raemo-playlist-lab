---
name: lines-clean
description: Apply rule-based cleaning to raw blog text and preview the resulting lyric lines. Use when you want to inspect or debug the cleaning step before building a full dataset.
argument-hint: [raw_txt_file_path]
arguments: [file_path]
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Read
---

## 목적

`data/raw/blog/*.txt` 파일에 7단계 정제 규칙을 적용해 가사 라인 목록을 미리보기 한다.

## 입력

- `$file_path`: raw blog txt 파일 경로  
  예: `data/raw/blog/a3f2c1d4b5e6f7a8.txt`

## 정제 규칙 (순서대로)

1. 빈 줄 제거
2. 이모지 시작 줄 제거 (플레이리스트 제목 등)
3. 구분선 제거 (`---`, `•••`, `...`, 등)
4. 이탤릭 코멘트 제거 (`*선곡 이유: ...*)
5. 번호 prefix 제거 (`1. ` → 내용만)
6. 괄호 코멘트 제거 (`(...)`, `[...]` 단독 줄)
7. 5자 미만 제거

## 출력

콘솔에 정제된 가사 라인 목록 출력 (번호 포함).

## 실행 절차

1. 아래 명령을 실행한다:

```bash
uv run python -m src.clean.lines "$file_path"
```

최소 길이를 바꾸려면:
```bash
uv run python -m src.clean.lines "$file_path" --min-length 3
```

2. 라인 수가 YouTube 트랙 수와 맞는지 확인한다.
3. 불필요한 줄이 남아 있으면 정제 규칙을 `src/clean/lines.py`에서 수정한다.

## 실패 처리

- 라인이 너무 적음: `--min-length` 줄이거나, 제거 규칙 비활성화 검토
- 라인이 너무 많음: 블로그 본문 구조 확인 → 새 제거 패턴 추가
