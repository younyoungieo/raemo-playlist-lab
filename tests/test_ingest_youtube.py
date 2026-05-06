"""Unit tests for src/ingest/youtube.py (no network calls)."""

import json
import pytest
from src.ingest.youtube import _playlist_id_from_url, TrackMeta


def test_extract_id_from_full_url():
    url = "https://www.youtube.com/playlist?list=PLxyz123ABC"
    assert _playlist_id_from_url(url) == "PLxyz123ABC"


def test_extract_id_from_url_with_extra_params():
    url = "https://www.youtube.com/playlist?v=abc&list=PLtest456&index=1"
    assert _playlist_id_from_url(url) == "PLtest456"


def test_passthrough_bare_id():
    assert _playlist_id_from_url("PLbareID789") == "PLbareID789"


def test_track_meta_typeddict():
    t: TrackMeta = {
        "position": 1,
        "video_id": "abc",
        "title": "테스트",
        "channel": "채널",
    }
    assert t["position"] == 1
    assert t["video_id"] == "abc"


SAMPLE_YTDLP_OUTPUT = {
    "entries": [
        {"id": "vid001", "title": "첫 번째 곡", "channel": "Artist A", "uploader": "Artist A"},
        {"id": "vid002", "title": "두 번째 곡", "channel": "Artist B", "uploader": "Artist B"},
        None,  # Deleted / private video shows as None in yt-dlp
        {"id": "vid004", "title": "네 번째 곡", "channel": "Artist C", "uploader": "Artist C"},
    ]
}


def test_none_entries_skipped(tmp_path, monkeypatch):
    """yt-dlp returns None for deleted/private videos; they should be skipped."""
    import subprocess
    import src.ingest.youtube as yt_module

    # Patch subprocess.run to return our fixture
    class FakeResult:
        stdout = json.dumps(SAMPLE_YTDLP_OUTPUT)

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: FakeResult())
    monkeypatch.setattr(yt_module, "CACHE_DIR", tmp_path)

    tracks = yt_module._fetch_via_ytdlp("PLtest")
    assert len(tracks) == 3  # None entry skipped
    assert tracks[0]["position"] == 1
    assert tracks[1]["position"] == 2
    assert tracks[2]["position"] == 4
