"""Weekly scrape of phdkim.net — page 1 of each board, threshold 20 likes.

Saves after every post so progress is never lost on API failure.
Re-running is safe: already-imported IDs are skipped automatically.
"""
import os
import sys
import time
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.storage import load_posts, save_posts, get_seen_ids
from scraper.translator import translate_text
from scraper.fetcher import fetch_paginated_board, fetch_post_detail
from scraper.html_gen import write_html

_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_LIKES_THRESHOLD = 20
_DELAY = 13.0      # free tier: 5 req/min for gemini-2.5-flash
_RETRIES = 4
_RETRY_WAIT = 60

_WEEKLY_BOARDS = [
    ("board/best/list", "Best board"),
    ("board/list",      "All boards"),
]


def _translate(text: str, api_key: str) -> str:
    for attempt in range(_RETRIES):
        try:
            return translate_text(text, api_key)
        except Exception as e:
            if attempt < _RETRIES - 1:
                print(f"    API error ({e}), retrying in {_RETRY_WAIT}s...")
                time.sleep(_RETRY_WAIT)
            else:
                raise


def _process_post(p: dict, posts: list, seen_ids: set, api_key: str, added: int) -> int:
    """Fetch detail, translate, save immediately. Returns new added count."""
    print(f"  [{added + 1}] {p['title_ko'][:55]} (👍 {p['likes']})")
    try:
        body_ko, date_str = fetch_post_detail(p["url"])
        p["date"] = date_str
        p["scraped_at"] = _date.today().isoformat()
        p["body_ko"] = body_ko
        p["title_zh"] = _translate(p["title_ko"], api_key)
        time.sleep(_DELAY)
        p["body_zh"] = _translate(body_ko, api_key)
        time.sleep(_DELAY)
        posts.append(p)
        seen_ids.add(p["id"])
        added += 1
        print(f"    → {p['title_zh'][:50]}")
        save_posts(posts)
    except Exception as e:
        print(f"    SKIP: {e}")
    return added


def run(api_key: str) -> int:
    """Execute weekly scrape. Returns number of new posts added."""
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    added = 0

    for board_path, label in _WEEKLY_BOARDS:
        print(f"\nFetching {label}...")
        try:
            board_posts = fetch_paginated_board(board_path, 1)
        except Exception as e:
            print(f"  ERROR: {e}, skipping board.")
            continue

        qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
        print(f"  {len(board_posts)} posts, {len(qualifying)} new and qualify (>= {_LIKES_THRESHOLD} likes)")

        for p in qualifying:
            added = _process_post(p, posts, seen_ids, api_key, added)

    write_html(posts, _HTML_PATH)
    print(f"\nDone. {added} new posts added. Total: {len(posts)}")
    return added


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
