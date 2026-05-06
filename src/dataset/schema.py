"""Pydantic v2 schema for the raemo playlist dataset."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class TrackItem(BaseModel):
    model_config = ConfigDict(strict=True)

    position: int
    youtube_video_id: str
    youtube_title: str
    youtube_channel: str
    lyric_line: str


class SourceInfo(BaseModel):
    model_config = ConfigDict(strict=True)

    playlist_id: str
    blog_post_url: str


class ValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    youtube_count: int
    lyric_line_count: int
    joined_count: int
    status: Literal["ok", "mismatch"]
    notes: str
    unmatched_youtube: list[int] = []   # positions with no lyric (yt > blog)
    unmatched_lyrics: list[str] = []    # lyric lines with no track (blog > yt)


class Dataset(BaseModel):
    model_config = ConfigDict(strict=True)

    playlist_key: str
    source: SourceInfo
    tracks: list[TrackItem]
    validation: ValidationResult
