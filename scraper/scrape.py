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
_DELAY = 13.0
_RETRIES = 3
_RETRY_WAIT = 60

# Boards checked each week: best board + all-boards list, page 1 only
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
                print(f"    Translation error ({e}), retrying in {_RETRY_WAIT}s...")
                time.sleep(_RETRY_WAIT)
            else:
                raise


def run(api_key: str) -> int:
    """Execute weekly scrape. Returns number of new posts added."""
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    new_posts = []
    skipped_posts = []

    for board_path, label in _WEEKLY_BOARDS:
        print(f"\nFetching {label}...")
        try:
            board_posts = fetch_paginated_board(board_path, 1)
        except Exception as e:
            print(f"  ERROR fetching {label}: {e}, skipping board.")
            continue

        candidates = [
            p for p in board_posts
            if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD
        ]
        print(f"  {len(board_posts)} posts found, {len(candidates)} new and qualify (>= {_LIKES_THRESHOLD} likes)")

        for p in candidates:
            print(f"  Processing: {p['title_ko'][:60]} (👍 {p['likes']})")
            try:
                body_ko, date = fetch_post_detail(p["url"])
                p["date"] = date
                p["scraped_at"] = _date.today().isoformat()
                p["body_ko"] = body_ko
                p["title_zh"] = _translate(p["title_ko"], api_key)
                time.sleep(_DELAY)
                p["body_zh"] = _translate(body_ko, api_key)
                time.sleep(_DELAY)
                new_posts.append(p)
                seen_ids.add(p["id"])
                print(f"    → {p['title_zh'][:50]}")
            except Exception as e:
                skipped_posts.append(f"{p['title_ko'][:50]} (👍{p['likes']})")
                print(f"::warning::⚠️ Skipped: {p['title_ko'][:50]} (👍{p['likes']}) — {e}")

    if new_posts:
        all_posts = posts + new_posts
        save_posts(all_posts)
        write_html(all_posts, _HTML_PATH)
        print(f"\nDone: {len(new_posts)} new posts added. Total: {len(all_posts)}")
    else:
        print("\nNo new posts found.")

    if skipped_posts:
        print(f"\n::warning::⚠️ {len(skipped_posts)} post(s) skipped due to errors — will retry next sync:")
        for title in skipped_posts:
            print(f"::warning::  - {title}")

    return len(new_posts)


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
