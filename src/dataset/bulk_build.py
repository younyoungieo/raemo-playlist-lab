"""Bulk-build datasets for all pending entries in playlist_index.json."""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from src.clean.lines import clean_lines
from src.dataset.builder import build_dataset, save_dataset
from src.ingest.blog import fetch_blog, fetch_youtube_url_from_blog
from src.ingest.blog_index import INDEX_PATH
from src.ingest.youtube import fetch_playlist


def load_index(path: str = INDEX_PATH) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: uv run python -m src.ingest.blog_index [blog_id] --save"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def save_index_status(entries: list[dict], path: str = INDEX_PATH) -> None:
    Path(path).write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def bulk_build(
    *,
    force_refresh: bool = False,
    dry_run: bool = False,
) -> None:
    entries = load_index()
    pending = [e for e in entries if e.get("status") == "pending"]

    if not pending:
        print("No pending entries. All done.")
        return

    print(f"Building {len(pending)} pending datasets...\n")

    for i, entry in enumerate(pending, 1):
        key = entry.get("playlist_key") or entry["log_no"]
        blog_url = entry["blog_url"]
        print(f"[{i}/{len(pending)}] {key}")
        print(f"  Blog: {blog_url}")

        if dry_run:
            print("  → (dry-run, skipping)\n")
            continue

        if not key:
            print("  ✗ playlist_key 없음 — status를 skip으로 설정하거나 키를 직접 입력하세요.\n")
            continue

        try:
            youtube_url = fetch_youtube_url_from_blog(blog_url, force_refresh=force_refresh)
            if not youtube_url:
                raise ValueError("블로그에서 YouTube URL을 찾을 수 없음")
            print(f"  YouTube: {youtube_url}")

            tracks = fetch_playlist(youtube_url, force_refresh=force_refresh)
            raw = fetch_blog(blog_url, force_refresh=force_refresh)
            lines = clean_lines(raw)

            dataset = build_dataset(key, youtube_url, blog_url, tracks, lines)
            path = save_dataset(dataset)

            v = dataset.validation
            status_str = f"✓ OK ({v.joined_count} tracks)" if v.status == "ok" else f"⚠ MISMATCH (yt={v.youtube_count}, blog={v.lyric_line_count})"
            print(f"  {status_str} → {path}")

            entry["status"] = "built" if v.status == "ok" else "mismatch"
            entry["validation_status"] = v.status
            entry["joined_count"] = v.joined_count

        except Exception as e:
            print(f"  ✗ 실패: {e}")
            entry["status"] = "error"
            entry["error"] = str(e)

        print()
        save_index_status(entries)

    built = sum(1 for e in entries if e.get("status") == "built")
    mismatch = sum(1 for e in entries if e.get("status") == "mismatch")
    errors = sum(1 for e in entries if e.get("status") == "error")
    still_pending = sum(1 for e in entries if e.get("status") == "pending")

    print("=" * 50)
    print(f"완료: {built}  /  mismatch: {mismatch}  /  오류: {errors}  /  pending: {still_pending}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bulk-build datasets from playlist_index.json")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be built without actually building")
    args = parser.parse_args()

    bulk_build(force_refresh=args.force_refresh, dry_run=args.dry_run)
