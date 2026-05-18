import json
from pathlib import Path

_DEFAULT_POSTS_FILE = Path(__file__).parent.parent / "data" / "posts.json"


def load_posts(posts_file: Path = _DEFAULT_POSTS_FILE) -> list:
    if not posts_file.exists():
        return []
    return json.loads(posts_file.read_text(encoding="utf-8"))


def save_posts(posts: list, posts_file: Path = _DEFAULT_POSTS_FILE) -> None:
    posts_file.write_text(
        json.dumps(posts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_seen_ids(posts: list) -> set:
    return {p["id"] for p in posts}
