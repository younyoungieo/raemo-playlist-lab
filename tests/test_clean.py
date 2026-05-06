"""Unit tests for src/clean/lines.py."""

import pytest
from src.clean.lines import CleanConfig, clean_lines


SAMPLE_BLOG_TEXT = """\
🎵 3월 첫 번째 플레이리스트
---
우리 둘이서 걷는 이 길
차가운 바람이 불어와도
1. 봄 햇살처럼
2. 그대 곁에 있어
...
*선곡 이유: 봄 감성*
(출처: 작사가 미상)
짧
"""


def test_basic_cleaning():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert "우리 둘이서 걷는 이 길" in lines
    assert "차가운 바람이 불어와도" in lines


def test_emoji_title_removed():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert not any(l.startswith("🎵") for l in lines)


def test_separator_removed():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert "---" not in lines
    assert "..." not in lines


def test_italic_comment_removed():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert not any(l.startswith("*") and l.endswith("*") for l in lines)


def test_bracket_comment_removed():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert "(출처: 작사가 미상)" not in lines


def test_number_prefix_stripped():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert "봄 햇살처럼" in lines
    assert "그대 곁에 있어" in lines
    assert not any(l.startswith("1.") or l.startswith("2.") for l in lines)


def test_short_line_removed():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    assert "짧" not in lines


def test_order_preserved():
    lines = clean_lines(SAMPLE_BLOG_TEXT)
    idx1 = lines.index("우리 둘이서 걷는 이 길")
    idx2 = lines.index("차가운 바람이 불어와도")
    assert idx1 < idx2


def test_custom_min_length():
    # "짧" is 1 char; min_length=1 lets it through
    cfg = CleanConfig(min_length=1)
    lines = clean_lines(SAMPLE_BLOG_TEXT, cfg)
    assert "짧" in lines


def test_empty_input():
    assert clean_lines("") == []


def test_only_separators():
    raw = "\n---\n•••\n...\n\n"
    assert clean_lines(raw) == []
