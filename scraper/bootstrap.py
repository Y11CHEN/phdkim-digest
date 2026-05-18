import os
import sys
from pathlib import Path
from datetime import date, datetime
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.storage import load_posts, save_posts, get_seen_ids
from scraper.translator import translate_text
from scraper.fetcher import fetch_board_page, fetch_post_detail
from scraper.html_gen import write_html

_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_LIKES_THRESHOLD = 150
_START_DATE = date(2024, 1, 1)


def _parse_date(date_str: str) -> date | None:
    """Parse common Korean forum date formats. Returns None if unparseable."""
    if not date_str:
        return None
    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def run(api_key: str) -> int:
    """Bootstrap initial data. Returns number of posts added."""
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    new_posts = []

    session = requests.Session()

    print("Fetching board for bootstrap...")
    board_posts = fetch_board_page(1, session)
    print(f"Found {len(board_posts)} posts. Filtering likes >= {_LIKES_THRESHOLD}...")

    for p in board_posts:
        if p["id"] in seen_ids:
            continue
        if p["likes"] < _LIKES_THRESHOLD:
            continue

        print(f"  Fetching detail: {p['title_ko'][:60]} (👍 {p['likes']})")
        body_ko, date_str = fetch_post_detail(p["url"], session)
        post_date = _parse_date(date_str)

        if post_date and post_date < _START_DATE:
            print(f"    Skipping: date {date_str} is before {_START_DATE}")
            continue

        p["date"] = date_str
        p["title_zh"] = translate_text(p["title_ko"], api_key)
        p["body_ko"] = body_ko
        p["body_zh"] = translate_text(body_ko, api_key)
        new_posts.append(p)
        seen_ids.add(p["id"])
        print(f"    Added: {p['title_zh']}")

    if new_posts:
        all_posts = posts + new_posts
        save_posts(all_posts)
        write_html(all_posts, _HTML_PATH)
        print(f"Bootstrap done: {len(new_posts)} posts added. Total: {len(all_posts)}")
    else:
        print("No posts to add.")

    return len(new_posts)


if __name__ == "__main__":
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        print("Error: DEEPL_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
