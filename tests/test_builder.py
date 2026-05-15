"""Unit tests for src/dataset/builder.py (no I/O)."""

import pytest
from src.dataset.builder import build_dataset
from src.ingest.youtube import TrackMeta


def _make_tracks(n: int) -> list[TrackMeta]:
    return [
        TrackMeta(position=i, video_id=f"vid{i:03}", title=f"곡 {i}", channel="ch")
        for i in range(1, n + 1)
    ]


def _make_lines(n: int) -> list[str]:
    return [f"가사 한 줄 {i}" for i in range(1, n + 1)]


def test_ok_when_counts_match():
    tracks = _make_tracks(3)
    lines = _make_lines(3)
    ds = build_dataset("key", "PLtest", "http://blog", tracks, lines)
    assert ds.validation.status == "ok"
    assert ds.validation.joined_count == 3
    assert ds.validation.notes == ""


def test_mismatch_youtube_more():
    tracks = _make_tracks(5)
    lines = _make_lines(3)
    ds = build_dataset("key", "PLtest", "http://blog", tracks, lines)
    assert ds.validation.status == "mismatch"
    assert ds.validation.joined_count == 3
    assert "YouTube" in ds.validation.notes


def test_blog_more_truncates_to_ok():
    # Blog has more lines than tracks → trailing content auto-truncated
    tracks = _make_tracks(3)
    lines = _make_lines(5)
    ds = build_dataset("key", "PLtest", "http://blog", tracks, lines)
    assert ds.validation.status == "ok"
    assert ds.validation.joined_count == 3
    assert "trailing" in ds.validation.notes


def test_position_join_correct():
    tracks = _make_tracks(3)
    lines = _make_lines(3)
    ds = build_dataset("key", "PLtest", "http://blog", tracks, lines)
    for track in ds.tracks:
        assert track.lyric_lines == [f"가사 한 줄 {track.position}"]


def test_lyric_lines_split_on_slash():
    tracks = _make_tracks(2)
    lines = ["가사1 / 가사2", "단일 가사"]
    ds = build_dataset("key", "PLtest", "http://blog", tracks, lines)
    assert ds.tracks[0].lyric_lines == ["가사1", "가사2"]
    assert ds.tracks[1].lyric_lines == ["단일 가사"]


def test_playlist_id_extracted_from_url():
    tracks = _make_tracks(1)
    lines = _make_lines(1)
    ds = build_dataset(
        "key",
        "https://youtube.com/playlist?list=PLxyz123",
        "http://blog",
        tracks,
        lines,
    )
    assert ds.source.playlist_id == "PLxyz123"


def test_empty_inputs():
    ds = build_dataset("key", "PLtest", "http://blog", [], [])
    assert ds.validation.status == "ok"
    assert ds.validation.joined_count == 0
