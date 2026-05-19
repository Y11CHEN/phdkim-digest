"""One-time script to retranslate all posts in posts.json using Gemini.

Reads existing Korean text (title_ko, body_ko) and overwrites the
Chinese translations (title_zh, body_zh) with Gemini output.
Saves after each post so progress is not lost if interrupted.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.storage import load_posts, save_posts
from scraper.translator import translate_text
from scraper.html_gen import write_html

_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_DELAY = 13.0  # free tier: 5 req/min for gemini-2.5-flash
_RETRIES = 4
_RETRY_WAIT = 15  # seconds to wait after a 503


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
    if not posts:
        print("No posts found in posts.json.")
        return

    print(f"Retranslating {len(posts)} posts with Gemini...\n")

    for i, post in enumerate(posts, 1):
        print(f"[{i}/{len(posts)}] {post['title_ko'][:55]}")
        post["title_zh"] = _translate(post["title_ko"], api_key)
        time.sleep(_DELAY)
        post["body_zh"] = _translate(post["body_ko"], api_key)
        time.sleep(_DELAY)
        print(f"  → {post['title_zh'][:50]}")
        save_posts(posts)

    write_html(posts, _HTML_PATH)
    print(f"\nDone. {len(posts)} posts retranslated and index.html regenerated.")


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run(api_key)
