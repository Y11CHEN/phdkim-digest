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
