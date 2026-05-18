from unittest.mock import MagicMock, patch

# HTML based on real phdkim.net board page structure.
# Selector: li.row > a.link (title/URL) + p.react span.text (likes)
BOARD_PAGE_HTML = """
<html><body>
<ul class="list">
  <li class="row">
    <a class="link ellipsis" href="/board/free/27703?from=home_hot_all">
      <span>[일반랩 vs 대가랩] 연구 및 논문비교</span>
    </a>
    <div class="info">
      <p class="react"><span class="text">383</span></p>
      <p class="comment"><span class="text">37</span></p>
    </div>
  </li>
  <li class="row">
    <a class="link ellipsis" href="/board/usadmission/2216?from=home_hot_all">
      <span>미국 이공계 박사 후기</span>
    </a>
    <div class="info">
      <p class="react"><span class="text">13</span></p>
      <p class="comment"><span class="text">3</span></p>
    </div>
  </li>
  <li class="row">
    <a class="link" href="/board/info/">공지사항</a>
  </li>
</ul>
</body></html>
"""

# HTML based on real phdkim.net post detail page structure.
# Body: div.content-area, date: p.date
POST_HTML = """
<html><body>
<div class="board-detail-page">
  <p class="date">2022.02.21</p>
  <div class="content-area">
    연구 경험을 공유합니다.<br/>
    대학원 생활은 쉽지 않습니다.<br/>
    하지만 배움이 있습니다.
  </div>
</div>
</body></html>
"""


def _make_mock_session(html: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()
    session = MagicMock()
    session.get.return_value = mock_resp
    return session


def test_fetch_board_page_returns_post_list():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_board_page
        session = _make_mock_session(BOARD_PAGE_HTML)
        posts = fetch_board_page(1, session)
    assert len(posts) == 2  # the /board/info/ item is filtered (non-numeric id)
    assert posts[0]["id"] == "27703"
    assert "phdkim.net" in posts[0]["url"]
    assert posts[0]["title_ko"] == "[일반랩 vs 대가랩] 연구 및 논문비교"
    assert posts[0]["likes"] == 383
    assert posts[0]["date"] == ""
    assert posts[1]["id"] == "2216"
    assert posts[1]["likes"] == 13


def test_fetch_board_page_url_is_absolute():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_board_page
        session = _make_mock_session(BOARD_PAGE_HTML)
        posts = fetch_board_page(1, session)
    for post in posts:
        assert post["url"].startswith("https://phdkim.net"), f"URL not absolute: {post['url']}"


def test_fetch_board_page_returns_empty_for_no_items():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_board_page
        session = _make_mock_session("<html><body></body></html>")
        posts = fetch_board_page(1, session)
    assert posts == []


def test_fetch_board_page_handles_missing_likes():
    html = """
    <html><body>
      <li class="row">
        <a class="link" href="/board/free/99999"><span>제목</span></a>
        <div class="info"></div>
      </li>
    </body></html>
    """
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_board_page
        session = _make_mock_session(html)
        posts = fetch_board_page(1, session)
    assert len(posts) == 1
    assert posts[0]["likes"] == 0


def test_fetch_post_content_returns_body_text():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_post_content
        session = _make_mock_session(POST_HTML)
        body = fetch_post_content("https://phdkim.net/board/free/27703", session)
    assert len(body) > 0
    assert "연구 경험" in body


def test_fetch_post_content_returns_empty_for_missing_body():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_post_content
        session = _make_mock_session("<html><body><p>no content area</p></body></html>")
        body = fetch_post_content("https://phdkim.net/board/free/1", session)
    assert body == ""


def test_fetch_post_detail_returns_body_and_date():
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_post_detail
        session = _make_mock_session(POST_HTML)
        body, date = fetch_post_detail("https://phdkim.net/board/free/27703", session)
    assert len(body) > 0
    assert date == "2022.02.21"


def test_fetch_post_detail_handles_missing_date():
    html = """
    <html><body>
      <div class="content-area">본문 내용입니다.</div>
    </body></html>
    """
    with patch("scraper.fetcher.time.sleep"):
        from scraper.fetcher import fetch_post_detail
        session = _make_mock_session(html)
        body, date = fetch_post_detail("https://phdkim.net/board/free/1", session)
    assert body == "본문 내용입니다."
    assert date == ""
