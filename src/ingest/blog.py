"""Naver blog post ingestion via requests + BeautifulSoup."""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

CACHE_DIR = Path("data/raw/blog")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# Naver blog selectors tried in order
_BODY_SELECTORS = [
    "div.se-main-container",   # Smart Editor 3 (현재 표준)
    "div#postViewArea",        # 구형 에디터
    "div.post-view",           # 일부 레이아웃
    "div#SE-content",          # Smart Editor 2
]


def _normalize_url(url: str) -> str:
    """Convert mobile Naver blog URL to PC version."""
    # m.blog.naver.com → blog.naver.com
    parsed = urlparse(url)
    host = parsed.netloc.replace("m.blog.", "blog.")
    return urlunparse(parsed._replace(netloc=host))


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:16]


def _cache_path(url: str) -> Path:
    return CACHE_DIR / f"{_url_hash(url)}.txt"

def _html_cache_path(url: str) -> Path:
    return CACHE_DIR / f"{_url_hash(url)}.html"


def _extract_text(html: str) -> str:
    """Parse HTML and return raw body text with newlines preserved."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for selector in _BODY_SELECTORS:
        container = soup.select_one(selector)
        if container:
            # Remove image captions (se-caption class inside se-section-image)
            for caption in container.select(".se-caption"):
                caption.decompose()
            for br in container.find_all("br"):
                br.replace_with("\n")
            for block in container.find_all(["p", "div", "li"]):
                block.append("\n")
            return container.get_text()

    return soup.get_text()


def _find_iframe_url(html: str, base: str = "https://blog.naver.com") -> str | None:
    """Return the absolute src of the first content iframe, if present."""
    soup = BeautifulSoup(html, "lxml")
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if "PostView" in src or "blogId" in src:
            return src if src.startswith("http") else base + src
    return None


def extract_youtube_url(html: str) -> str | None:
    """Return the first YouTube playlist URL found in the blog post body, or None."""
    soup = BeautifulSoup(html, "lxml")
    container = soup.select_one("div.se-main-container") or soup
    for a in container.find_all("a", href=True):
        href = a["href"]
        if "youtube.com/playlist" in href or "youtu.be" in href:
            return href
    return None


def fetch_blog(url: str, *, force_refresh: bool = False) -> str:
    """Fetch and return raw body text of a public Naver blog post.

    Results are cached in data/raw/blog/{hash}.txt.
    """
    return _fetch_blog_inner(url, force_refresh=force_refresh)[0]


def fetch_youtube_url_from_blog(url: str, *, force_refresh: bool = False) -> str | None:
    """Return the YouTube playlist URL embedded in the blog post, or None."""
    return _fetch_blog_inner(url, force_refresh=force_refresh)[1]


def _fetch_blog_inner(url: str, *, force_refresh: bool = False) -> tuple[str, str | None]:
    """Core fetch: returns (body_text, youtube_url_or_none). Caches both."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = _normalize_url(url)
    text_cache = _cache_path(url)
    html_cache = _html_cache_path(url)

    if html_cache.exists() and not force_refresh:
        html = html_cache.read_text(encoding="utf-8")
        text = _extract_text(html)
        text_cache.write_text(text, encoding="utf-8")
        return text, extract_youtube_url(html)

    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()

    iframe_url = _find_iframe_url(resp.text)
    if iframe_url:
        iframe_headers = {**_HEADERS, "Referer": url}
        resp = requests.get(iframe_url, headers=iframe_headers, timeout=15)
        resp.raise_for_status()

    html = resp.text
    text = _extract_text(html)
    if not text.strip():
        raise ValueError(f"Empty body extracted from {url}. May require login or JS rendering.")

    text_cache.write_text(text, encoding="utf-8")
    html_cache.write_text(html, encoding="utf-8")
    time.sleep(0.5)
    return text, extract_youtube_url(html)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Naver blog post body text")
    parser.add_argument("url", help="Naver blog post URL")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    raw = fetch_blog(args.url, force_refresh=args.force_refresh)
    lines = [l for l in raw.splitlines() if l.strip()]
    print(f"Extracted {len(lines)} non-empty lines (raw, before cleaning)")
    for line in lines[:10]:
        print(f"  {line[:80]}")
    if len(lines) > 10:
        print(f"  ... ({len(lines) - 10} more)")
