"""Validate an existing dataset and print a diff report."""

from __future__ import annotations

import json
from pathlib import Path

from src.dataset.schema import Dataset

DATASETS_DIR = Path("data/datasets")


def load_dataset(playlist_key: str) -> Dataset:
    path = DATASETS_DIR / f"{playlist_key}.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return Dataset.model_validate_json(path.read_text(encoding="utf-8"))


def print_report(dataset: Dataset) -> None:
    v = dataset.validation
    print(f"=== Validation Report: {dataset.playlist_key} ===")
    print(f"  YouTube tracks  : {v.youtube_count}")
    print(f"  Blog lyric lines: {v.lyric_line_count}")
    print(f"  Joined tracks   : {v.joined_count}")
    print(f"  Status          : {v.status.upper()}")

    if v.notes:
        print(f"  Note            : {v.notes}")

    if v.status == "mismatch":
        _print_sidebyside(dataset)
        _print_correction_hint(dataset)


def _print_sidebyside(dataset: Dataset) -> None:
    """Print a side-by-side comparison of all YouTube tracks vs lyric lines."""
    v = dataset.validation
    track_map = {t.position: t for t in dataset.tracks}
    max_pos = max(v.youtube_count, v.lyric_line_count)

    print(f"\n  {'POS':>3}  {'YOUTUBE TITLE':<40}  {'LYRIC LINE'}")
    print(f"  {'---':>3}  {'-'*40}  {'-'*40}")

    for pos in range(1, max_pos + 1):
        track = track_map.get(pos)
        yt_title = (track.youtube_title[:38] + "..") if track and len(track.youtube_title) > 40 else (track.youtube_title if track else "── (no track) ──")

        if pos <= v.joined_count:
            lyric = " / ".join(track.lyric_lines) if track else ""
            flag = "✓"
        elif pos <= v.youtube_count:
            lyric = "── (가사 없음) ──"
            flag = "⚠ 가사 누락"
        else:
            extra_idx = pos - v.youtube_count - 1
            lyric = v.unmatched_lyrics[extra_idx] if extra_idx < len(v.unmatched_lyrics) else "?"
            flag = "⚠ 트랙 없음"

        lyric_short = (lyric[:38] + "..") if len(lyric) > 40 else lyric
        print(f"  [{pos:>3}]  {yt_title:<40}  {lyric_short}  {flag}")


def _print_correction_hint(dataset: Dataset) -> None:
    """Print instructions for creating a corrections file."""
    from src.dataset.builder import OVERRIDES_DIR
    v = dataset.validation
    override_path = OVERRIDES_DIR / f"{dataset.playlist_key}.json"

    print(f"\n  --- 수정 방법 ---")
    print(f"  {override_path} 파일을 만들어 아래 형식으로 보정값을 입력하세요:")
    print(f"""
  {{
    "lyric_overrides": {{
      "3": "직접 입력할 가사",   // 가사 수정
      "5": null                  // 가사 없는 곡 (빈 문자열로 처리)
    }},
    "skip_positions": []         // 데이터셋에서 제외할 position 번호
  }}
""")
    print(f"  수정 후 /dataset-build {dataset.playlist_key} [blog_url] 로 재빌드하세요.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate a raemo playlist dataset")
    parser.add_argument("playlist_key", help="e.g. 26_Mar_1st")
    args = parser.parse_args()

    dataset = load_dataset(args.playlist_key)
    print_report(dataset)
