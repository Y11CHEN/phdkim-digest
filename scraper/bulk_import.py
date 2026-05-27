"""Bulk import of 100+ like posts from the best board (/board/best/list).

Scans every page from newest to oldest, skips posts already in posts.json,
fetches detail + translates for any post with likes >= threshold,
and stops when it hits an empty page.
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
_MAX_PAGES = 9999  # effectively unlimited; stops on empty page


def run(api_key: str) -> int:
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    new_posts = []

    session = requests.Session()

    for page in range(1, _MAX_PAGES + 1):
        print(f"Page {page}...", end=" ", flush=True)
        try:
            board_posts = fetch_best_board_page(page, session)
        except Exception as e:
            print(f"ERROR: {e}, skipping")
            time.sleep(5)
            continue

        if not board_posts:
            print("empty, done.")
            break

        qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
        print(f"{len(board_posts)} posts, {len(qualifying)} qualify")

        for p in qualifying:
            print(f"  Fetching: {p['title_ko'][:55]} (👍 {p['likes']})")
            try:
                body_ko, date_str = fetch_post_detail(p["url"], session)
                p["date"] = date_str
                p["scraped_at"] = _date.today().isoformat()
                p["body_ko"] = body_ko
                for attempt in range(3):
                    try:
                        p["title_zh"] = translate_text(p["title_ko"], api_key)
                        time.sleep(13)
                        p["body_zh"] = translate_text(body_ko, api_key)
                        time.sleep(13)
                        break
                    except Exception as te:
                        if attempt < 2:
                            print(f"    Translation error ({te}), retrying in 60s...")
                            time.sleep(60)
                        else:
                            raise
                new_posts.append(p)
                seen_ids.add(p["id"])
                print(f"    Added: {p['title_zh']}")
            except Exception as e:
                print(f"    ERROR: {e}, skipping")

        # Save progress every 5 pages so a crash doesn't lose everything
        if new_posts and page % 5 == 0:
            all_posts = posts + new_posts
            save_posts(all_posts)
            write_html(all_posts, _HTML_PATH)
            print(f"  [checkpoint] saved {len(new_posts)} new posts so far")

    if new_posts:
        all_posts = posts + new_posts
        save_posts(all_posts)
        write_html(all_posts, _HTML_PATH)
        print(f"\nDone: {len(new_posts)} posts added. Total: {len(all_posts)}")
    else:
        print("\nNo new posts found.")

    return len(new_posts)


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
