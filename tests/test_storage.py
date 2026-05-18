import json
import pytest
from pathlib import Path


def test_load_posts_returns_empty_list_when_file_missing(tmp_path):
    from scraper.storage import load_posts
    assert load_posts(tmp_path / "posts.json") == []


def test_save_and_load_roundtrip(tmp_path):
    from scraper.storage import save_posts, load_posts
    posts_file = tmp_path / "posts.json"
    posts = [{"id": "1", "title_zh": "标题", "likes": 10}]
    save_posts(posts, posts_file)
    assert load_posts(posts_file) == posts


def test_save_uses_utf8_encoding(tmp_path):
    from scraper.storage import save_posts
    posts_file = tmp_path / "posts.json"
    posts = [{"id": "1", "title_zh": "한국어中文テスト", "likes": 5}]
    save_posts(posts, posts_file)
    raw = posts_file.read_text(encoding="utf-8")
    assert "한국어中文テスト" in raw


def test_get_seen_ids_returns_set_of_ids():
    from scraper.storage import get_seen_ids
    posts = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    assert get_seen_ids(posts) == {"1", "2", "3"}


def test_get_seen_ids_empty():
    from scraper.storage import get_seen_ids
    assert get_seen_ids([]) == set()
