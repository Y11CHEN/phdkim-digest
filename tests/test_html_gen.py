from pathlib import Path


SAMPLE_POSTS = [
    {
        "id": "1", "title_zh": "高赞标题", "likes": 100,
        "date": "2026-01-01", "url": "https://phdkim.net/1",
        "body_zh": "正文内容",
    },
    {
        "id": "2", "title_zh": "低赞标题", "likes": 10,
        "date": "2026-01-02", "url": "https://phdkim.net/2",
        "body_zh": "另一篇正文",
    },
]


def test_generate_html_contains_all_titles():
    from scraper.html_gen import generate_html
    html = generate_html(SAMPLE_POSTS)
    assert "高赞标题" in html
    assert "低赞标题" in html


def test_generate_html_sorts_by_likes_descending():
    from scraper.html_gen import generate_html
    html = generate_html(SAMPLE_POSTS)
    assert html.index("高赞标题") < html.index("低赞标题")


def test_generate_html_contains_original_url():
    from scraper.html_gen import generate_html
    html = generate_html(SAMPLE_POSTS)
    assert "https://phdkim.net/1" in html


def test_generate_html_collapses_long_body():
    from scraper.html_gen import generate_html
    long_post = [{
        "id": "3", "title_zh": "长文章", "likes": 50,
        "date": "2026-01-03", "url": "https://phdkim.net/3",
        "body_zh": "字" * 600,
    }]
    html = generate_html(long_post)
    assert "<details>" in html
    assert "继续阅读..." in html


def test_generate_html_no_details_for_short_body():
    from scraper.html_gen import generate_html
    short_post = [{
        "id": "4", "title_zh": "短文章", "likes": 50,
        "date": "2026-01-04", "url": "https://phdkim.net/4",
        "body_zh": "字" * 100,
    }]
    html = generate_html(short_post)
    assert "<details>" not in html


def test_write_html_creates_file(tmp_path):
    from scraper.html_gen import write_html
    output = tmp_path / "index.html"
    write_html(SAMPLE_POSTS, output)
    assert output.exists()
    assert "高赞标题" in output.read_text(encoding="utf-8")


GROUPED_POSTS = [
    {
        "id": "10", "title_zh": "本周帖子", "likes": 80,
        "date": "2026-05-18", "url": "https://phdkim.net/10",
        "body_zh": "内容A", "scraped_at": "2026-05-18",
    },
    {
        "id": "11", "title_zh": "上周帖子", "likes": 90,
        "date": "2026-05-11", "url": "https://phdkim.net/11",
        "body_zh": "内容B", "scraped_at": "2026-05-11",
    },
    {
        "id": "12", "title_zh": "历史帖子", "likes": 200,
        "date": "2025-01-01", "url": "https://phdkim.net/12",
        "body_zh": "内容C",
    },
]


def test_group_header_appears_for_weekly_batch():
    from scraper.html_gen import generate_html
    html = generate_html(GROUPED_POSTS)
    assert "2026-05-18" in html
    assert "2026-05-11" in html


def test_historical_group_header_appears():
    from scraper.html_gen import generate_html
    html = generate_html(GROUPED_POSTS)
    assert "历史精选" in html


def test_newest_batch_appears_before_older_batch():
    from scraper.html_gen import generate_html
    html = generate_html(GROUPED_POSTS)
    assert html.index("2026-05-18") < html.index("2026-05-11")


def test_weekly_batches_appear_before_historical():
    from scraper.html_gen import generate_html
    html = generate_html(GROUPED_POSTS)
    assert html.index("2026-05-18") < html.index("历史精选")


def test_within_group_sorted_by_likes():
    from scraper.html_gen import generate_html
    same_batch = [
        {"id": "20", "title_zh": "低赞同批", "likes": 55,
         "date": "2026-05-18", "url": "https://phdkim.net/20",
         "body_zh": "x", "scraped_at": "2026-05-18"},
        {"id": "21", "title_zh": "高赞同批", "likes": 120,
         "date": "2026-05-18", "url": "https://phdkim.net/21",
         "body_zh": "y", "scraped_at": "2026-05-18"},
    ]
    html = generate_html(same_batch)
    assert html.index("高赞同批") < html.index("低赞同批")
