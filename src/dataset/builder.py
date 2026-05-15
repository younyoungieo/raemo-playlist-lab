"""Build a Dataset by position-joining YouTube tracks and lyric lines."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.dataset.schema import Dataset, SourceInfo, TrackItem, ValidationResult
from src.ingest.blog import fetch_youtube_url_from_blog
from src.ingest.youtube import TrackMeta


DATASETS_DIR = Path("data/datasets")
OVERRIDES_DIR = Path("data/overrides")


def _playlist_id_from_url(url_or_id: str) -> str:
    match = re.search(r"[?&]list=([A-Za-z0-9_-]+)", url_or_id)
    return match.group(1) if match else url_or_id


def _load_corrections(playlist_key: str) -> dict:
    """Load manual corrections from data/overrides/{playlist_key}.json if it exists.

    Format:
    {
      "lyric_overrides": {"3": "수정 가사", "5": null},
      "skip_positions": [7]
    }
    """
    path = OVERRIDES_DIR / f"{playlist_key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def build_dataset(
    playlist_key: str,
    youtube_url_or_id: str,
    blog_post_url: str,
    tracks: list[TrackMeta],
    lyric_lines: list[str],
) -> Dataset:
    """Position-join tracks and lyric_lines into a Dataset.

    If data/overrides/{playlist_key}.json exists, applies manual corrections
    before finalizing (lyric_overrides, skip_positions).
    """
    playlist_id = _playlist_id_from_url(youtube_url_or_id)
    corrections = _load_corrections(playlist_key)
    lyric_overrides: dict[int, str | None] = {
        int(k): v for k, v in corrections.get("lyric_overrides", {}).items()
    }
    skip_positions: set[int] = set(corrections.get("skip_positions", []))

    # Full lyric_lines override: replaces blog extraction entirely
    if "lyric_lines" in corrections:
        lyric_lines = corrections["lyric_lines"]

    yt_count = len(tracks)
    notes_parts: list[str] = []

    # Truncate trailing non-lyric content when blog has more lines than tracks
    if len(lyric_lines) > yt_count:
        excess = len(lyric_lines) - yt_count
        lyric_lines = lyric_lines[:yt_count]
        notes_parts.append(f"trailing {excess}줄 제거")

    line_count = len(lyric_lines)
    joined_count = min(yt_count, line_count)

    joined: list[TrackItem] = []
    for i in range(joined_count):
        t = tracks[i]
        pos = t["position"]
        if pos in skip_positions:
            parts: list[str] = []
        elif pos in lyric_overrides:
            raw = lyric_overrides[pos]
            if raw is None:
                parts = []
            elif isinstance(raw, list):
                parts = [p.strip() for p in raw if p]
            else:
                parts = [p.strip() for p in str(raw).split(" / ") if p.strip()]
        else:
            raw_line = lyric_lines[i]
            parts = [p.strip() for p in raw_line.split(" / ")] if raw_line else []
        joined.append(
            TrackItem(
                position=pos,
                youtube_video_id=t["video_id"],
                youtube_title=t["title"],
                youtube_channel=t["channel"],
                lyric_lines=parts,
            )
        )

    unmatched_youtube = [tracks[i]["position"] for i in range(joined_count, yt_count)]
    unmatched_lyrics: list[str] = []

    if yt_count > line_count:
        diff = yt_count - line_count
        notes_parts.append(f"YouTube has {diff} extra tracks (가사 누락 의심)")

    validation = ValidationResult(
        youtube_count=yt_count,
        lyric_line_count=line_count,
        joined_count=joined_count,
        status="ok" if yt_count == line_count else "mismatch",
        notes=" | ".join(notes_parts),
        unmatched_youtube=unmatched_youtube,
        unmatched_lyrics=unmatched_lyrics,
    )

    return Dataset(
        playlist_key=playlist_key,
        source=SourceInfo(playlist_id=playlist_id, blog_post_url=blog_post_url),
        tracks=joined,
        validation=validation,
    )


def save_dataset(dataset: Dataset) -> Path:
    """Write dataset JSON to data/datasets/{playlist_key}.json and return the path."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    out = DATASETS_DIR / f"{dataset.playlist_key}.json"
    out.write_text(
        dataset.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return out


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    from src.clean.lines import clean_lines
    from src.ingest.blog import fetch_blog
    from src.ingest.youtube import fetch_playlist

    parser = argparse.ArgumentParser(description="Build a raemo playlist dataset")
    parser.add_argument("playlist_key", help="e.g. 26_Mar_1st")
    parser.add_argument("blog_url", help="Naver blog post URL")
    parser.add_argument("youtube_url", nargs="?", default=None,
                        help="YouTube playlist URL or ID (optional — auto-extracted from blog if omitted)")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    youtube_url = args.youtube_url
    if not youtube_url:
        print(f"[1/4] Extracting YouTube URL from blog…")
        youtube_url = fetch_youtube_url_from_blog(args.blog_url, force_refresh=args.force_refresh)
        if not youtube_url:
            print("      ERROR: No YouTube playlist URL found in blog post.")
            raise SystemExit(1)
        print(f"      Found: {youtube_url}")
    else:
        print(f"[1/4] Fetching YouTube playlist…")

    tracks = fetch_playlist(youtube_url, force_refresh=args.force_refresh)
    print(f"      {len(tracks)} tracks found")

    print(f"[2/4] Fetching blog post…")
    raw = fetch_blog(args.blog_url, force_refresh=args.force_refresh)

    print(f"[3/4] Cleaning lyric lines…")
    lines = clean_lines(raw)
    print(f"      {len(lines)} lyric lines after cleaning")

    print(f"[4/4] Building dataset…")
    dataset = build_dataset(
        args.playlist_key,
        youtube_url,
        args.blog_url,
        tracks,
        lines,
    )
    path = save_dataset(dataset)
    print(f"      Saved → {path}")
    print(f"\nValidation: {dataset.validation.status.upper()}")
    print(f"  YouTube:  {dataset.validation.youtube_count}")
    print(f"  Blog:     {dataset.validation.lyric_line_count}")
    print(f"  Joined:   {dataset.validation.joined_count}")
    if dataset.validation.notes:
        print(f"  Note:     {dataset.validation.notes}")
