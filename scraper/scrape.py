import os
import sys
import time
from datetime import date as _date
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.storage import load_posts, save_posts, get_seen_ids
from scraper.translator import translate_text
from scraper.fetcher import fetch_board_page, fetch_post_detail
from scraper.html_gen import write_html

_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_LIKES_THRESHOLD = 50


def run(api_key: str) -> int:
    """Execute weekly scrape. Returns number of new posts added."""
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    new_posts = []

    session = requests.Session()

    # phdkim.net returns the same hot-posts snapshot regardless of page number.
    # One fetch is all we need.
    print("Fetching board...")
    board_posts = fetch_board_page(1, session)
    print(f"Found {len(board_posts)} posts on board.")

    for p in board_posts:
        if p["id"] in seen_ids:
            continue
        if p["likes"] < _LIKES_THRESHOLD:
            continue

        print(f"  Processing: {p['title_ko'][:60]} (👍 {p['likes']})")
        body_ko, date = fetch_post_detail(p["url"], session)
        p["date"] = date
        p["scraped_at"] = _date.today().isoformat()
        p["body_ko"] = body_ko
        try:
            p["title_zh"] = translate_text(p["title_ko"], api_key)
            time.sleep(13)
            p["body_zh"] = translate_text(body_ko, api_key)
            time.sleep(13)
        except Exception as e:
            print(f"    Translation failed ({e}), skipping post.")
            continue
        new_posts.append(p)
        seen_ids.add(p["id"])

    if new_posts:
        all_posts = posts + new_posts
        save_posts(all_posts)
        write_html(all_posts, _HTML_PATH)
        print(f"Done: {len(new_posts)} new posts added. Total: {len(all_posts)}")
    else:
        print("No new posts found.")

    return len(new_posts)


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
