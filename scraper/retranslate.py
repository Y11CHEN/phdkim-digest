  """phdkim.net scraper — historical full import and weekly digest.

  Historical mode (default):
    Scans all pages of best board, impact board, all boards.
    Likes threshold: 100. Run once to seed data.

  Weekly mode (--weekly):
    Scans page 1 only of best board and all boards.
    Likes threshold: 20. Run by GitHub Actions every Monday.

  Saves after each post so progress is not lost if interrupted.
  Re-running is safe: already-imported IDs are skipped automatically.
  """
  import argparse
  import os
  import sys
  import time
  from datetime import date as _date
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent.parent))

  from scraper.storage import load_posts, save_posts, get_seen_ids
  from scraper.translator import translate_text
  from scraper.fetcher import fetch_paginated_board, fetch_impact_board, fetch_post_detail
  from scraper.html_gen import write_html

  _HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
  _LIKES_THRESHOLD = 100
  _LIKES_THRESHOLD_WEEKLY = 20
  _DELAY = 13.0
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
          print(f"    →{p['title_zh'][:50]}")
          save_posts(posts)
      except Exception as e:
          print(f"    SKIP: {e}")
      return added


  def _scrape_paginated(board_path: str, label: str, posts: list, seen_ids: set,
                        api_key: str, added: int, threshold: int) -> int:
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

          qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= threshold]
          print(f"{len(board_posts)} posts, {len(qualifying)} qualify")

          for p in qualifying:
              added = _process_post(p, posts, seen_ids, api_key, added)

      return added


  def run(api_key: str) -> None:
      """Historical full import: all pages, threshold 100."""
      posts = load_posts()
      seen_ids = get_seen_ids(posts)
      added = 0

      added = _scrape_paginated("board/best/list", "Best board", posts, seen_ids, api_key, added, _LIKES_THRESHOLD)

      print("\n--- Impact board (JS rendering) ---")
      try:
          impact_posts = fetch_impact_board()
          qualifying = [p for p in impact_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD]
          print(f"{len(impact_posts)} posts found, {len(qualifying)} qualify")
          for p in qualifying:
              added = _process_post(p, posts, seen_ids, api_key, added)
      except Exception as e:
          print(f"Impact board ERROR: {e}")

      added = _scrape_paginated("board/list", "All boards", posts, seen_ids, api_key, added, _LIKES_THRESHOLD)

      write_html(posts, _HTML_PATH)
      print(f"\nDone. {added} new posts added. Total: {len(posts)}")


  def run_weekly(api_key: str) -> None:
      """Weekly digest: page 1 only of each board, threshold 20."""
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

          qualifying = [p for p in board_posts if p["id"] not in seen_ids and p["likes"] >= _LIKES_THRESHOLD_WEEKLY]
          print(f"  {len(board_posts)} posts, {len(qualifying)} new and qualify (>= {_LIKES_THRESHOLD_WEEKLY}
  likes)")

          for p in qualifying:
              added = _process_post(p, posts, seen_ids, api_key, added)

      write_html(posts, _HTML_PATH)
      print(f"\nDone. {added} new posts added. Total: {len(posts)}")


  if __name__ == "__main__":
      parser = argparse.ArgumentParser()
      parser.add_argument("--weekly", action="store_true", help="Run weekly digest mode")
      args = parser.parse_args()

      api_key = os.environ.get("GEMINI_API_KEY")
      if not api_key:
          print("Error: GEMINI_API_KEY environment variable not set.")
          sys.exit(1)

      if args.weekly:
          run_weekly(api_key)
      else:
          run(api_key)
