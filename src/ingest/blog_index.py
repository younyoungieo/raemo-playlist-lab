"""Naver blog post index: list all [Playlist] posts for a given blog."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from urllib.parse import unquote

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
_LIST_URL = "https://blog.naver.com/PostTitleListAsync.naver"
_COUNT_PER_PAGE = 30

# Matches keys like: 26_Apr_1st  25_Dec_2nd  24_Jan_1st
_RE_PLAYLIST_KEY = re.compile(r"\d{2}_[A-Za-z]{3}_\w+")


@dataclass
class PostInfo:
    log_no: str
    title: str          # full title without [Playlist] prefix, spaces restored
    playlist_key: str   # e.g. "26_Apr_1st" (empty string if not found)
    date: str           # "2026. 5. 4."
    url: str            # https://blog.naver.com/{blog_id}/{log_no}


def _decode_title(raw: str) -> str:
    """URL-decode and replace + with space."""
    return unquote(raw).replace("+", " ")


def _extract_key(title_without_prefix: str) -> str:
    """Extract playlist key from title, e.g. '26_Apr_1st 망설임은...' → '26_Apr_1st'."""
    m = _RE_PLAYLIST_KEY.search(title_without_prefix)
    return m.group(0).rstrip("_") if m else ""


def _parse_response(text: str) -> list[dict]:
    """Parse Naver's slightly-broken JSON (contains invalid \\' escapes)."""
    return json.loads(text.replace("\\'", "'"))["postList"]


def list_playlist_posts(
    blog_id: str,
    *,
    prefix: str = "[Playlist]",
    max_pages: int = 50,
) -> list[PostInfo]:
    """Return all blog posts whose title starts with `prefix`, newest first."""
    results: list[PostInfo] = []

    for page in range(1, max_pages + 1):
        resp = requests.get(
            _LIST_URL,
            params={
                "blogId": blog_id,
                "categoryNo": 0,
                "currentPage": page,
                "countPerPage": _COUNT_PER_PAGE,
            },
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        posts = _parse_response(resp.text)

        for p in posts:
            title = _decode_title(p["title"])
            if not title.startswith(prefix):
                continue
            body = title[len(prefix):].strip()
            results.append(
                PostInfo(
                    log_no=p["logNo"],
                    title=body,
                    playlist_key=_extract_key(body),
                    date=p["addDate"],
                    url=f"https://blog.naver.com/{blog_id}/{p['logNo']}",
                )
            )

        if len(posts) < _COUNT_PER_PAGE:
            break
        time.sleep(0.3)

    return results


INDEX_PATH = "data/playlist_index.json"


def save_index(posts: list[PostInfo], path: str = INDEX_PATH) -> None:
    """Save post list to a JSON index file for bulk management.

    Existing entries are preserved: only new log_nos are appended,
    and existing status/overrides are not overwritten.
    """
    from pathlib import Path
    import json

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict] = {}
    if p.exists():
        for entry in json.loads(p.read_text(encoding="utf-8")):
            existing[entry["log_no"]] = entry

    merged = []
    for post in posts:
        if post.log_no in existing:
            merged.append(existing[post.log_no])
        else:
            merged.append({
                "playlist_key": post.playlist_key,
                "blog_url": post.url,
                "title": post.title,
                "date": post.date,
                "log_no": post.log_no,
                "status": "pending",  # pending | built | skip
            })

    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(merged)} entries → {path}")
    new_count = len(merged) - len(existing)
    if new_count:
        print(f"  ({new_count} new entries added)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List all [Playlist] posts from a Naver blog")
    parser.add_argument("blog_id", help="Naver blog ID, e.g. janjanjae")
    parser.add_argument("--prefix", default="[Playlist]")
    parser.add_argument("--save", action="store_true", help=f"Save to {INDEX_PATH}")
    args = parser.parse_args()

    posts = list_playlist_posts(args.blog_id, prefix=args.prefix)
    print(f"Found {len(posts)} posts with prefix '{args.prefix}'\n")
    for p in posts:
        key_str = f"[{p.playlist_key}]" if p.playlist_key else "[key?]"
        print(f"  {p.date}  {key_str:<20}  {p.title[:45]}")

    if args.save:
        print()
        save_index(posts)
