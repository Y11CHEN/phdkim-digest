"""Historical full scrape of phdkim.net best board.

Scans every page from newest to oldest, skips posts already in posts.json,
fetches detail + translates for any post with likes >= threshold,
and stops when it hits an empty page.
Saves after each post so progress is not lost if interrupted.
Re-running is safe: already-imported IDs are skipped automatically.
"""
import os
import sys
import time
from datetime import date as _date
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.storage import load_posts, save_posts, get_seen_ids
from scraper.translator import translate_text
from scraper.fetcher import fetch_best_board_page, fetch_post_detail
from scraper.html_gen import write_html

_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_LIKES_THRESHOLD = 100
_DELAY = 13.0      # free tier: 5 req/min for gemini-2.5-flash
_RETRIES = 4
_RETRY_WAIT = 60


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


def run(api_key: str) -> None:
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    added = 0

    session = requests.Session()

    for page in range(1, 10000):
        print(f"Page {page}...", end=" ", flush=True)
        try:
            board_posts = fetch_best_board_page(page, session)
        except Exception as e:
            print(f"ERROR: {e}, retrying in 10s...")
            time.sleep(10)
            continue

        if not board_posts:
            print("empty, done.")
            break

        qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
        print(f"{len(board_posts)} posts, {len(qualifying)} qualify")

        for p in qualifying:
            print(f"  [{added + 1}] {p['title_ko'][:55]} (👍 {p['likes']})")
            try:
                body_ko, date_str = fetch_post_detail(p["url"], session)
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

    write_html(posts, _HTML_PATH)
    print(f"\nDone. {added} new posts added. Total: {len(posts)}")


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
