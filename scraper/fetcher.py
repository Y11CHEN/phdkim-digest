import time
import random
from bs4 import BeautifulSoup
from scrapling import Fetcher, StealthyFetcher

_BASE_URL = "https://phdkim.net"


def _fetch(url: str) -> BeautifulSoup | None:
    """Fetch page with scrapling. Returns None on 404, raises on other errors."""
    page = Fetcher.get(url, stealthy_headers=True)
    time.sleep(random.uniform(2, 5))
    if page.status == 404:
        return None
    return BeautifulSoup(page.html_content, "html.parser")


def _fetch_stealth(url: str) -> BeautifulSoup:
    """JS-rendered fetch via headless browser (for pages requiring JavaScript)."""
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
    return BeautifulSoup(page.html_content, "html.parser")


def _parse_item_title_row(row) -> dict | None:
    """Parse a li.row that uses a.item-title. Returns None if not a valid post."""
    link = row.select_one("a.item-title")
    if not link:
        return None
    href = link.get("href", "").split("?")[0]
    parts = [p for p in href.split("/") if p]
    if len(parts) < 3 or not parts[-1].isdigit():
        return None
    board_type = parts[-2]          # 'best', 'free', etc.
    post_id = f"{board_type}_{parts[-1]}"
    title_ko = link.get_text(strip=True)
    likes_el = row.select_one("p.reacted")
    try:
        likes = int(likes_el.get_text(strip=True).replace(",", ""))
    except (AttributeError, ValueError):
        likes = 0
    return {
        "id": post_id,
        "url": f"{_BASE_URL}{href}",
        "title_ko": title_ko,
        "likes": likes,
        "date": "",
    }


def fetch_paginated_board(board_path: str, page_num: int) -> list[dict]:
    """Fetch one page of any paginated board. Returns [] at end (404 or empty).

    board_path examples: 'board/best/list', 'board/list', 'board/free/list'
    Post IDs are derived from URL path: board_type + '_' + numeric_id.
    """
    soup = _fetch(f"{_BASE_URL}/{board_path}/{page_num}")
    if soup is None:
        return []
    posts = []
    for row in soup.select("li.row"):
        post = _parse_item_title_row(row)
        if post:
            posts.append(post)
    return posts


def fetch_best_board_page(page_num: int, session=None) -> list[dict]:
    """Fetch one page from /board/best/list. (session param kept for compat, ignored)"""
    return fetch_paginated_board("board/best/list", page_num)


def fetch_impact_board(session=None) -> list[dict]:
    """Fetch all posts from /board/impact/list using full JS rendering.

    Returns the complete hall-of-fame list (180+ posts back to 2019).
    Uses StealthyFetcher so JavaScript-loaded posts are included.
    """
    soup = _fetch_stealth(f"{_BASE_URL}/board/impact/list")
    posts = []
    for row in soup.select("li.row"):
        link = row.select_one("a.link")
        if not link:
            continue
        href = link.get("href", "").split("?")[0]
        parts = [p for p in href.split("/") if p]
        if len(parts) < 3 or not parts[-1].isdigit():
            continue
        board_type = parts[-2]
        post_id = f"{board_type}_{parts[-1]}"
        title_ko = link.get_text(strip=True)
        likes_el = row.select_one("p.react span.text")
        try:
            likes = int(likes_el.get_text(strip=True).replace(",", ""))
        except (AttributeError, ValueError):
            likes = 0
        posts.append({
            "id": post_id,
            "url": f"{_BASE_URL}{href}",
            "title_ko": title_ko,
            "likes": likes,
            "date": "",
        })
    return posts


def fetch_post_detail(url: str, session=None) -> tuple[str, str]:
    """Returns (body_text, date_str). (session param kept for compat, ignored)"""
    soup = _fetch(url)
    if soup is None:
        return "", ""
    body_el = soup.select_one("div.content-area")
    body = body_el.get_text(separator="\n", strip=True) if body_el else ""
    date_el = soup.select_one("p.date")
    date = date_el.get_text(strip=True) if date_el else ""
    return body, date


def fetch_board_page(page_num: int, session=None) -> list[dict]:
    """Deprecated wrapper — use fetch_paginated_board instead."""
    return fetch_paginated_board("board/list", page_num)
