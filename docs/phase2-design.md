# Phase 2 설계 문서: 가사 기반 무드 검색 시스템

> 전체 로드맵: [roadmap.md](./roadmap.md)
> Phase 1 (데이터 파이프라인)은 완료. 44개 플레이리스트 → JSON 데이터셋 23개 유효.

## 1. 목표

Phase 1에서 만든 44개 플레이리스트 데이터셋(23개 유효)을 기반으로,
자연어 무드 쿼리로 어울리는 트랙을 검색하는 시스템을 만든다.

**핵심 시나리오:**
> "비 오는 날 혼자 듣기 좋은" → 관련 트랙 + 가사 한 줄 반환

**배포 방향 (장기):**
사용자가 자신의 YouTube 플레이리스트를 넣으면 무드를 분석하고 비슷한 감성의 트랙을 추천하는 서비스. 지금은 래모 데이터셋만으로 로컬 검증.

---

## 2. 리서치 기반 결정사항

### 임베딩 모델

| 후보 | 장점 | 단점 | 결정 |
|------|------|------|------|
| `jhgan/ko-sroberta-multitask` | KorSTS 85.60, 경량(~500MB), 한국어 특화 | 영어 가사에서 품질 저하 가능 | **1순위** |
| `dragonkue/BGE-m3-ko` | 한/영 혼합 강점, 최신 다국어 MTEB 우수 | 무거움(~2GB), 추론 느림 | 영어 비중 높으면 전환 |
| `intfloat/multilingual-e5-large` | 경량, 다국어 | BGE-M3보다 한국어 품질 소폭 낮음 | 3순위 |

→ **시작: `ko-sroberta-multitask`**, 영어 쿼리 품질 불충분하면 `bge-m3-ko`로 전환.
→ 컬렉션 이름에 모델 버전 포함 (`raemo_kosroberta_v1`).

### 인덱싱 단위

- **트랙 단위 ❌**: 가사가 평균화되어 특색 소실, 검색 결과 설명 불가
- **줄 단위 ✅**: `lyric_lines` 배열의 각 줄이 별도 document. "이 줄 때문에 이 트랙이 나왔다" 설명 가능

→ 1 lyric line = 1 ChromaDB document

### 검색 방식

- 230개 트랙 × 평균 2줄 = ~460 documents → brute force cosine similarity (<1ms)
- BM25 hybrid, reranking: 이 규모에서 오버킬
- **쿼리 확장**: 선택적. LLM으로 "비 오는 날" → "gray/우울/쓸쓸/rain" 추가

### 레퍼런스 프로젝트

- **Wawes** (wawes.vercel.app): YouTube 플레이리스트 + 무드 쿼리 검색, MVP 6시간 구현
- **Lyric-Based Music Finder**: ChromaDB + BERT, 가장 유사한 구조
- **Musical Word Embedding** (seungheondoh): 한국 연구자, 청취 컨텍스트 ↔ 음악 임베딩

---

## 3. 무드 분류 체계

Spotify 2D 모델을 한국 감성에 맞게 적용:

```
1차축 (Phase 3, 자동 계산):
  에너지:    잔잔 ↔ 활기
  감정방향:  슬픔 ↔ 행복

2차 레이어 (Phase 2, LLM 자동 태깅):
  상황: 새벽 | 퇴근길 | 드라이브 | 카페 | 이별 후 | 혼자
  감정 서사: 그리움 | 위로 | 설렘 | 공허 | 따뜻함

3차 (Phase 3, 장기):
  감성 프로파일: "당신은 새벽-위로-인디 타입"
```

### LLM 자동 태깅

- `lyric_lines` + `youtube_title` + `youtube_channel`을 컨텍스트로 LLM 호출
- 결과를 `data/mood_tags/{playlist_key}.json`에 캐시 (Phase 1 overrides 패턴과 동일)
- 수동 교정: `data/mood_overrides/{playlist_key}.json`으로 덮어쓰기 가능

```json
// data/mood_tags/26_Mar_1st.json
{
  "3": {
    "situation": ["새벽", "혼자"],
    "emotion": ["그리움", "위로"]
  }
}
```

```json
// data/mood_overrides/26_Mar_1st.json  (선택적 수동 교정)
{
  "3": {
    "situation": ["카페"],
    "emotion": ["설렘"]
  }
}
```

태깅 시점: 인덱싱 전 일괄 처리 → ChromaDB metadata에 포함시켜 필터링에 활용.

---

## 4. 데이터 흐름

```
data/datasets/{playlist_key}.json  (Phase 1 출력)
        │
        ▼
[indexer]  src/recommend/indexer.py
  - lyric_lines 줄 단위 분리
  - 빈 lyric_lines 트랙 제외 (skip 엔트리 등)
  - 각 줄 임베딩 → ChromaDB 저장
        │
        ▼
data/chromadb/  (로컬 영속 저장)
  collection: raemo_kosroberta_v1
        │
        ▼
[searcher]  src/recommend/searcher.py
  - 쿼리 텍스트 임베딩
  - cosine similarity 검색
  - 결과 역참조: ChromaDB metadata → 원본 트랙 정보
        │
        ▼
SearchResult: [{ track, lyric_line, score, playlist_key }]
```

---

## 5. ChromaDB 스키마

### Document (검색 대상)
```
document:  "비가 내려도 괜찮아"       ← lyric_line 텍스트
```

### Metadata (필터/역참조용)
```json
{
  "playlist_key":      "26_Mar_1st",
  "position":          3,
  "line_index":        0,
  "youtube_video_id":  "abc123",
  "youtube_title":     "곡 제목",
  "youtube_channel":   "채널명"
}
```

### ID
```
{playlist_key}__{position}__{line_index}
예: 26_Mar_1st__3__0
```

---

## 6. 모듈 구조

```
src/recommend/
├── __init__.py
├── indexer.py       # datasets → ChromaDB 인덱스 빌드
├── searcher.py      # 쿼리 → 트랙 검색
└── schema.py        # SearchResult, IndexStats Pydantic 모델
```

CLI 진입점:
```bash
# 인덱스 빌드
uv run python -m src.recommend.indexer [--force-rebuild]

# 검색
uv run python -m src.recommend.searcher "비 오는 날 혼자 듣기 좋은"
```

---

## 7. 출력 스키마 (SearchResult)

```json
{
  "query": "비 오는 날 혼자 듣기 좋은",
  "results": [
    {
      "rank": 1,
      "score": 0.87,
      "lyric_line": "비가 내려도 괜찮아",
      "line_index": 0,
      "track": {
        "position": 3,
        "youtube_video_id": "abc123",
        "youtube_title": "곡 제목",
        "youtube_channel": "채널명",
        "playlist_key": "26_Mar_1st"
      }
    }
  ],
  "model": "jhgan/ko-sroberta-multitask",
  "total_documents": 460
}
```

---

## 8. 다양성 보장

같은 플레이리스트 트랙이 Top-K를 독점하는 문제를 두 가지 레이어로 처리:

### 검색 시 다양성 (playlist_key 분산)

Top-K 결과에서 같은 `playlist_key`가 연속으로 나오면, 해당 플레이리스트의 추가 결과를 후순위로 밀고 다른 플레이리스트 결과로 채움.

```
예: Top-5 결과가 26_Mar_1st × 3개라면
→ 26_Mar_1st 2개 유지 + 다른 playlist_key에서 3개 보충
```

### 노출 빈도 기록 (retrieval_count)

- 각 document에 `retrieval_count` 필드를 별도 stats 파일로 추적
- `data/chromadb/retrieval_stats.json` — document ID별 누적 노출 횟수
- 검색 결과에 `retrieval_count` 포함 → 수동 점검 시 "이 가사가 너무 자주 노출되고 있지 않은지" 확인 가능
- 선택적으로 빈도에 역가중치 적용해서 덜 노출된 트랙 우선 노출 가능

```json
// data/chromadb/retrieval_stats.json
{
  "26_Mar_1st__3__0": 12,
  "25_Jan_2nd__7__1": 3
}
```

---

## 9. 주요 엣지 케이스

| 케이스 | 처리 |
|--------|------|
| `lyric_lines: []` 트랙 | 인덱싱 제외 |
| `lyric_lines` 1줄짜리 트랙 | 그대로 1 document |
| 같은 `playlist_key` 트랙이 Top-K 독점 | 섹션 8 다양성 보장 로직 적용 |
| 영어 쿼리 → 한국어 가사 검색 | multilingual 모델이 기본 처리, 품질 낮으면 모델 전환 |
| 모델 변경 시 | 컬렉션 재빌드 (컬렉션 이름에 모델 버전 포함) |

---

## 10. 비목표 (Phase 2)

- LLM 쿼리 확장 (선택적으로 나중에)
- 무드 자동 태깅 (1차축 자동 분류)
- 웹 UI / API 서버
- 사용자 플레이리스트 입력 (장기 배포 기능)
- 오디오 피처 기반 분류

---

## 11. 열린 질문

- [ ] `ko-sroberta-multitask` vs `bge-m3-ko`: 실제 쿼리 몇 개 테스트 후 결정
- [ ] retrieval_count 역가중치: Phase 2에서 적용할지 Phase 3으로 미룰지
- [ ] 쿼리 확장 (LLM): Phase 2에서 할지 Phase 3으로 미룰지
- [ ] LLM 태깅 프롬프트 설계: 태그 후보 고정 목록 vs 자유 생성 후 정규화
