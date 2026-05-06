"""YouTube playlist ingestion via yt-dlp."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

CACHE_DIR = Path("data/raw/youtube")


class TrackMeta(TypedDict):
    position: int
    video_id: str
    title: str
    channel: str


def _playlist_id_from_url(url_or_id: str) -> str:
    """Extract playlist ID from a full URL or return the ID as-is."""
    match = re.search(r"[?&]list=([A-Za-z0-9_-]+)", url_or_id)
    return match.group(1) if match else url_or_id


def _cache_path(playlist_id: str) -> Path:
    return CACHE_DIR / f"{playlist_id}.json"


def _fetch_via_ytdlp(playlist_id: str) -> list[TrackMeta]:
    """Run yt-dlp --flat-playlist and parse output."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-J", "--no-warnings", url],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    entries = data.get("entries") or []
    tracks: list[TrackMeta] = []
    for idx, entry in enumerate(entries, start=1):
        if entry is None:
            continue
        tracks.append(
            TrackMeta(
                position=idx,
                video_id=entry.get("id") or "",
                title=entry.get("title") or "",
                channel=entry.get("channel") or entry.get("uploader") or "",
            )
        )
    return tracks


def fetch_playlist(
    url_or_id: str,
    *,
    force_refresh: bool = False,
) -> list[TrackMeta]:
    """Return track list for a YouTube playlist.

    Results are cached in data/raw/youtube/{playlist_id}.json.
    Pass force_refresh=True to bypass the cache.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    playlist_id = _playlist_id_from_url(url_or_id)
    cache = _cache_path(playlist_id)

    if cache.exists() and not force_refresh:
        return json.loads(cache.read_text(encoding="utf-8"))

    tracks = _fetch_via_ytdlp(playlist_id)
    cache.write_text(json.dumps(tracks, ensure_ascii=False, indent=2), encoding="utf-8")
    return tracks


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest a YouTube playlist via yt-dlp")
    parser.add_argument("url_or_id", help="Playlist URL or ID")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    tracks = fetch_playlist(args.url_or_id, force_refresh=args.force_refresh)
    print(f"Fetched {len(tracks)} tracks")
    for t in tracks[:5]:
        print(f"  [{t['position']:>3}] {t['video_id']}  {t['title'][:50]}")
    if len(tracks) > 5:
        print(f"  ... ({len(tracks) - 5} more)")
