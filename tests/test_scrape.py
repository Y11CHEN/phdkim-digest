import datetime
from unittest.mock import patch


def test_scraped_at_is_set_on_new_posts():
    from scraper.scrape import run

    today = datetime.date.today().isoformat()
    saved = []
    mock_board_posts = [
        {"id": "99", "url": "http://phdkim.net/99", "title_ko": "테스트", "likes": 60}
    ]

    with patch("scraper.scrape.load_posts", return_value=[]), \
         patch("scraper.scrape.get_seen_ids", return_value=set()), \
         patch("scraper.scrape.fetch_board_page", return_value=mock_board_posts), \
         patch("scraper.scrape.fetch_post_detail", return_value=("body text", "2026.05.18")), \
         patch("scraper.scrape.translate_text", return_value="translated"), \
         patch("scraper.scrape.save_posts", side_effect=lambda posts: saved.extend(posts)), \
         patch("scraper.scrape.write_html"), \
         patch("scraper.scrape.requests"):
        run("fake_key")

    assert len(saved) == 1
    assert saved[0]["scraped_at"] == today
