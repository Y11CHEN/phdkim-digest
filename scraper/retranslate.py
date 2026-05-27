"""Historical full scrape of phdkim.net — covers all major boards.

Boards scraped (in order):
  1. /board/best/list  — best board, paginated (already fully imported)
  2. /board/list       — all sub-boards combined, paginated, back to platform founding
  3. /board/impact/list — IF Hall of Fame, JS-rendered, 180+ all-time posts

Saves after each post so progress is not lost if interrupted.
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
from scraper.fetcher import fetch_best_board_page, fetch_paginated_board, fetch_impact_board, fetch_post_detail
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


def _process_post(p: dict, posts: list, seen_ids: set, api_key: str, added: int) -> int:
    """Fetch detail, translate, save. Returns new added count."""
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


def _scrape_paginated(board_path: str, label: str, posts: list, seen_ids: set,
                      api_key: str, added: int) -> int:
    """Scan all pages of a paginated board until empty or 404."""
    print(f"\n--- {label} ({board_path}) ---")
    for page in range(1, 10000):
        print(f"Page {page}...", end=" ", flush=True)
        try:
            board_posts = fetch_paginated_board(board_path, page)
        except Exception as e:
            print(f"ERROR: {e}, retrying in 10s...")
            time.sleep(10)
            continue

        if not board_posts:
            print("done.")
            break

        qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
        print(f"{len(board_posts)} posts, {len(qualifying)} qualify")

        for p in qualifying:
            added = _process_post(p, posts, seen_ids, api_key, added)

    return added


def run(api_key: str) -> None:
    posts = load_posts()
    seen_ids = get_seen_ids(posts)
    added = 0

    # 1. Best board (paginated, already fully imported — fast pass)
    added = _scrape_paginated("board/best/list", "Best board", posts, seen_ids, api_key, added)

    # 2. Impact board (JS-rendered single page, all-time hall of fame)
    # Run before /board/list so its IDs land in seen_ids first, preventing duplicates
    print("\n--- Impact board (IF 명예의 전당, JS rendering) ---")
    try:
        impact_posts = fetch_impact_board()
        qualifying = [p for p in impact_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
        print(f"{len(impact_posts)} posts found, {len(qualifying)} qualify")
        for p in qualifying:
            added = _process_post(p, posts, seen_ids, api_key, added)
    except Exception as e:
        print(f"Impact board ERROR: {e}")

    # 3. All-boards list (paginated, covers free + other sub-boards back to founding)
    # Impact board IDs are already in seen_ids, so overlapping posts are skipped automatically
    added = _scrape_paginated("board/list", "All boards", posts, seen_ids, api_key, added)

    write_html(posts, _HTML_PATH)
    print(f"\nDone. {added} new posts added. Total: {len(posts)}")


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
