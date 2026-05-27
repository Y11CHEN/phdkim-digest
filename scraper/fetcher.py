import time
import random
import requests
from bs4 import BeautifulSoup

_BASE_URL = "https://phdkim.net"
_BOARD_URL = f"{_BASE_URL}/board"
_BEST_BOARD_URL = f"{_BASE_URL}/board/best/list"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _get(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    time.sleep(random.uniform(2, 5))
    return BeautifulSoup(resp.text, "html.parser")


def fetch_board_page(page_num: int, session: requests.Session) -> list[dict]:
    """Returns list of {id, url, title_ko, likes, date} from the board hot-posts feed.

    Note: phdkim.net does not expose a chronological paginated feed in its server-rendered
    HTML.  The board homepage returns a curated 'hot posts' snapshot; page_num is accepted
    for API compatibility but does not change the result set (the site ignores ?page=N).
    The 'date' field is not present on listing rows and is returned as an empty string;
    call fetch_post_detail() to obtain the date for a specific post.
    """
    url = f"{_BOARD_URL}?page={page_num}"
    soup = _get(session, url)

    posts = []
    for row in soup.select("li.row"):
        link = row.select_one("a.link")
        if not link:
            continue

        href = link.get("href", "")
        if not href or "/board/" not in href:
            continue

        post_url = href if href.startswith("http") else f"{_BASE_URL}{href}"
        # Strip query params to get canonical URL and extract ID
        clean_href = href.split("?")[0]
        post_id = clean_href.rstrip("/").split("/")[-1]
        if not post_id.isdigit():
            continue

        title_el = link.select_one("span")
        title_ko = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)

        likes_el = row.select_one("p.react span.text")
        try:
            likes = int(likes_el.get_text(strip=True).replace(",", ""))
        except (AttributeError, ValueError):
            likes = 0

        posts.append({
            "id": post_id,
            "url": post_url,
            "title_ko": title_ko,
            "likes": likes,
            "date": "",
        })

    return posts


def fetch_best_board_page(page_num: int, session: requests.Session) -> list[dict]:
    """Returns posts from /board/best/list/{page_num}.

    The best board uses different selectors from the main board:
    a.item-title for titles and p.reacted for likes. IDs are prefixed
    with 'best_' to avoid collisions with main-board IDs.
    Returns empty list when page has no posts (past the last page).
    """
    url = f"{_BEST_BOARD_URL}/{page_num}"
    soup = _get(session, url)

    posts = []
    for row in soup.select("li.row"):
        link = row.select_one("a.item-title")
        if not link:
            continue

        href = link.get("href", "")
        if not href or "/board/best/" not in href:
            continue

        clean_href = href.split("?")[0]
        raw_id = clean_href.rstrip("/").split("/")[-1]
        if not raw_id.isdigit():
            continue

        post_url = f"{_BASE_URL}{clean_href}"
        post_id = f"best_{raw_id}"
        title_ko = link.get_text(strip=True)

        likes_el = row.select_one("p.reacted")
        try:
            likes = int(likes_el.get_text(strip=True).replace(",", ""))
        except (AttributeError, ValueError):
            likes = 0

        posts.append({
            "id": post_id,
            "url": post_url,
            "title_ko": title_ko,
            "likes": likes,
            "date": "",
        })

    return posts


def fetch_impact_board(session: requests.Session) -> list[dict]:
    """Returns all posts from /board/impact/list (single page, no pagination).

    The impact board aggregates high-engagement posts from all sub-boards.
    IDs are prefixed with the sub-board name (e.g. 'free_28190') to avoid
    collision with best board IDs ('best_N').
    """
    soup = _get(session, f"{_BASE_URL}/board/impact/list")
    posts = []
    for row in soup.select("li.row"):
        link = row.select_one("a.link")
        if not link:
            continue
        href = link.get("href", "").split("?")[0]
        parts = [p for p in href.split("/") if p]
        if len(parts) < 3 or not parts[-1].isdigit():
            continue
        board_type = parts[-2]
        post_url = f"{_BASE_URL}{href}"
        post_id = f"{board_type}_{parts[-1]}"
        title_ko = link.get_text(strip=True)
        likes_el = row.select_one("p.react span.text")
        try:
            likes = int(likes_el.get_text(strip=True).replace(",", ""))
        except (AttributeError, ValueError):
            likes = 0
        posts.append({
            "id": post_id,
            "url": post_url,
            "title_ko": title_ko,
            "likes": likes,
            "date": "",
        })
    return posts


def fetch_post_detail(url: str, session: requests.Session) -> tuple[str, str]:
    """Returns (body_text, date_str) for a post.  date_str is in 'YYYY.MM.DD' format
    or empty string if not found.
    """
    soup = _get(session, url)

    body_el = soup.select_one("div.content-area")
    body = body_el.get_text(separator="\n", strip=True) if body_el else ""

    date_el = soup.select_one("p.date")
    date = date_el.get_text(strip=True) if date_el else ""

    return body, date
