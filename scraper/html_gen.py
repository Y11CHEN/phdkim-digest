from datetime import datetime, timezone
from pathlib import Path
import html as _html

_DEFAULT_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_BODY_COLLAPSE_THRESHOLD = 500


def generate_html(posts: list) -> str:
    posts_sorted = sorted(posts, key=lambda p: p["likes"], reverse=True)
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(posts_sorted)

    cards = []
    for p in posts_sorted:
        title = _html.escape(p["title_zh"])
        url = p["url"]  # URL: keep as-is (it's from our own scraper)
        likes = p["likes"]  # integer: safe
        date = _html.escape(p["date"])
        body = _html.escape(p.get("body_zh", ""))

        if len(body) > _BODY_COLLAPSE_THRESHOLD:
            preview = body[:_BODY_COLLAPSE_THRESHOLD]
            rest = body[_BODY_COLLAPSE_THRESHOLD:]
            body_html = (
                f'<p>{preview}</p>'
                f'<details><summary>继续阅读...</summary>'
                f'<p>{rest}</p></details>'
            )
        else:
            body_html = f'<p>{body}</p>'

        cards.append(
            f'<div class="post">'
            f'<div class="post-title"><a href="{url}" target="_blank">{title}</a></div>'
            f'<div class="post-meta">👍 {likes} &nbsp;|&nbsp; {date}</div>'
            f'<div class="post-body">{body_html}</div>'
            f'</div>'
        )

    posts_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>phdkim.net 中文精选</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:820px;margin:0 auto;padding:20px 16px;background:#f0f2f5;color:#333}}
header{{margin-bottom:24px}}
h1{{margin:0 0 4px;font-size:22px}}
header p{{color:#888;margin:0;font-size:13px}}
.post{{background:#fff;border-radius:10px;padding:20px;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.post-title{{font-size:17px;font-weight:600;margin:0 0 6px}}
.post-title a{{color:#1a1a1a;text-decoration:none}}
.post-title a:hover{{text-decoration:underline}}
.post-meta{{color:#aaa;font-size:12px;margin-bottom:12px}}
.post-body p{{margin:0;line-height:1.75;white-space:pre-wrap;color:#444}}
details{{margin-top:8px}}
details summary{{cursor:pointer;color:#888;font-size:13px;user-select:none}}
</style>
</head>
<body>
<header>
  <h1>phdkim.net 中文精选</h1>
  <p>最后更新：{updated_at} &nbsp;|&nbsp; 共 {total} 篇</p>
</header>
{posts_html}
</body>
</html>"""


def write_html(posts: list, output_path: Path = _DEFAULT_HTML_PATH) -> None:
    output_path.write_text(generate_html(posts), encoding="utf-8")
