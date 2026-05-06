"""Rule-based lyric line cleaner for Naver blog text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TypedDict

# Regex compiled once at module load
_RE_EMOJI_START = re.compile(
    r"^[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0000FE00-\U0000FEFF]"
)
_RE_SEPARATOR = re.compile(r"^[\-=•·※~\s]+$|^\.\.\.*$|^[_\-]{2,}$")
_RE_ITALIC_COMMENT = re.compile(r"^\*[^*]+\*$")
_RE_NUMBER_PREFIX = re.compile(r"^\d+[\.\)]\s+")
_RE_BRACKET_COMMENT = re.compile(r"^\([^)]+\)$|^\[[^\]]+\]$")
_RE_URL = re.compile(r"^https?://|^[\w.-]+\.(com|net|org|kr|co\.kr|io|me)/?$")
_RE_PLAYLIST_KEY = re.compile(r"^\d{2}_[A-Za-z]")

MIN_LENGTH = 5  # characters after strip+clean


@dataclass
class CleanConfig:
    """Toggle individual cleaning rules on/off."""
    remove_empty: bool = True
    remove_emoji_title: bool = True
    remove_separator: bool = True
    remove_italic_comment: bool = True
    strip_number_prefix: bool = True
    remove_bracket_comment: bool = True
    remove_url: bool = True
    remove_playlist_key: bool = True
    min_length: int = MIN_LENGTH


def _is_removed(line: str, cfg: CleanConfig) -> bool:
    if cfg.remove_empty and not line:
        return True
    if cfg.remove_emoji_title and _RE_EMOJI_START.match(line):
        return True
    if cfg.remove_separator and _RE_SEPARATOR.match(line):
        return True
    if cfg.remove_italic_comment and _RE_ITALIC_COMMENT.match(line):
        return True
    if cfg.remove_bracket_comment and _RE_BRACKET_COMMENT.match(line):
        return True
    if cfg.remove_url and _RE_URL.match(line):
        return True
    if cfg.remove_playlist_key and _RE_PLAYLIST_KEY.match(line):
        return True
    return False


def _strip_prefix(line: str, cfg: CleanConfig) -> str:
    if cfg.strip_number_prefix:
        line = _RE_NUMBER_PREFIX.sub("", line)
    return line


def clean_lines(raw_text: str, cfg: CleanConfig | None = None) -> list[str]:
    """Apply rule-based cleaning to raw blog body text.

    Returns a list of lyric lines in original order.
    """
    if cfg is None:
        cfg = CleanConfig()

    result: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()

        if _is_removed(line, cfg):
            continue

        line = _strip_prefix(line, cfg)
        line = line.strip()

        if len(line) < cfg.min_length:
            continue

        result.append(line)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Clean lyric lines from raw blog text")
    parser.add_argument("file", help="Path to raw .txt file")
    parser.add_argument("--min-length", type=int, default=MIN_LENGTH)
    args = parser.parse_args()

    raw = Path(args.file).read_text(encoding="utf-8")
    cfg = CleanConfig(min_length=args.min_length)
    lines = clean_lines(raw, cfg)
    print(f"Cleaned: {len(lines)} lyric lines")
    for i, ln in enumerate(lines, 1):
        print(f"  [{i:>3}] {ln}")
