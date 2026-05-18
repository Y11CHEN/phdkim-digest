from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import html as _html

_DEFAULT_HTML_PATH = Path(__file__).parent.parent / "docs" / "index.html"
_BODY_COLLAPSE_THRESHOLD = 500


def _group_posts(posts: list) -> list[tuple[str, list]]:
    """Return [(group_label, posts_in_group), ...] — weekly groups newest-first, historical last."""
    weekly: dict[str, list] = defaultdict(list)
    historical = []
    for p in posts:
        sat = p.get("scraped_at", "")
        if sat:
            weekly[sat].append(p)
        else:
            historical.append(p)

    groups = []
    for date_str in sorted(weekly.keys(), reverse=True):
        group_posts = sorted(weekly[date_str], key=lambda p: p.get("likes", 0), reverse=True)
        groups.append((f"{date_str} · {len(group_posts)} 篇", group_posts))

    if historical:
        historical_sorted = sorted(historical, key=lambda p: p.get("likes", 0), reverse=True)
        groups.append((f"历史精选（初始导入）· {len(historical_sorted)} 篇", historical_sorted))

    return groups


def _render_card(p: dict) -> str:
    post_id = _html.escape(str(p["id"]))
    title = _html.escape(p["title_zh"])
    url = _html.escape(p["url"])
    likes = p.get("likes", 0)
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

    return (
        f'<div class="post" data-id="{post_id}">'
        f'<div class="post-header" onclick="toggleAccordion(this.closest(\'.post\'))">'
        f'<div class="post-title">'
        f'<a href="{url}" target="_blank" onclick="event.stopPropagation()">{title}</a>'
        f'</div>'
        f'<div class="post-right">'
        f'<span class="post-meta">👍 {likes} &nbsp;|&nbsp; {date}</span>'
        f'<button class="fav-btn" data-id="{post_id}" '
        f'onclick="event.stopPropagation();toggleFav(this)" title="收藏">☆</button>'
        f'</div>'
        f'</div>'
        f'<div class="post-body">{body_html}</div>'
        f'</div>'
    )


def generate_html(posts: list) -> str:
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(posts)

    sections = []
    for group_label, group_posts in _group_posts(posts):
        header = f'<div class="group-header">{_html.escape(group_label)}</div>'
        cards = "\n".join(_render_card(p) for p in group_posts)
        sections.append(header + "\n" + cards)

    posts_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>phdkim.net 中文精选</title>
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:820px;margin:0 auto;padding:20px 16px;background:#f0f2f5;color:#333}}
header{{margin-bottom:20px}}
h1{{margin:0 0 4px;font-size:22px}}
.subtitle{{color:#888;margin:0 0 14px;font-size:13px}}
.tabs{{display:flex;gap:6px;flex-wrap:wrap}}
.tab{{padding:6px 18px;border-radius:20px;border:1.5px solid #ddd;background:#fff;cursor:pointer;font-size:14px;color:#555}}
.tab:hover{{border-color:#aaa}}
.tab.active{{background:#222;color:#fff;border-color:#222}}
.group-header{{font-size:13px;color:#888;font-weight:600;margin:20px 0 8px;padding-left:6px;border-left:3px solid #d0d0d0}}
.post{{background:#fff;border-radius:10px;padding:16px 20px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.post-header{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
.post-title{{font-size:16px;font-weight:600;flex:1;min-width:0;margin:0}}
.post-title a{{color:#1a1a1a;text-decoration:none;word-break:break-word}}
.post-title a:hover{{text-decoration:underline}}
.post-right{{display:flex;align-items:center;gap:8px;flex-shrink:0;padding-top:2px}}
.post-meta{{color:#aaa;font-size:12px;white-space:nowrap}}
.fav-btn{{background:none;border:none;font-size:20px;cursor:pointer;padding:0;line-height:1;color:#ddd;transition:color .1s}}
.fav-btn:hover{{color:#f5a623}}
.fav-btn.active{{color:#f5a623}}
.post-body{{margin-top:12px}}
.post-body p{{margin:0;line-height:1.75;white-space:pre-wrap;color:#444}}
details{{margin-top:8px}}
details summary{{cursor:pointer;color:#888;font-size:13px;user-select:none}}
body[data-view="toc"] .post-header{{cursor:pointer}}
body[data-view="toc"] .post.expanded{{box-shadow:0 2px 8px rgba(0,0,0,.12)}}
.fav-empty{{text-align:center;padding:60px 20px;color:#aaa;background:#fff;border-radius:10px;display:none}}
</style>
</head>
<body data-view="toc">
<header>
  <h1>phdkim.net 中文精选</h1>
  <p class="subtitle">最后更新：{updated_at} &nbsp;|&nbsp; 共 {total} 篇</p>
  <div class="tabs">
    <button class="tab active" id="tab-toc" onclick="switchView('toc')">目录</button>
    <button class="tab" id="tab-full" onclick="switchView('full')">全文</button>
    <button class="tab" id="tab-fav" onclick="switchView('fav')">收藏<span id="fav-badge"></span></button>
  </div>
</header>
{posts_html}
<div class="fav-empty" id="fav-empty">还没有收藏 &nbsp;·&nbsp; 点击帖子右侧的 ☆ 来收藏</div>
<script>
function getFavs(){{try{{return new Set(JSON.parse(localStorage.getItem('phdkim_favs')||'[]'))}}catch(e){{return new Set()}}}}
function saveFavs(f){{localStorage.setItem('phdkim_favs',JSON.stringify([...f]))}}
function switchView(v){{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+v).classList.add('active');
  document.body.dataset.view=v;
  sessionStorage.setItem('phdkim_view',v);
  applyView();
}}
function applyView(){{
  var v=document.body.dataset.view,favs=getFavs(),n=0;
  document.querySelectorAll('.post').forEach(function(post){{
    var id=post.dataset.id,body=post.querySelector('.post-body');
    if(v==='fav'){{
      var show=favs.has(id);
      post.style.display=show?'':'none';
      if(show){{body.style.display='';n++}}
    }}else{{
      post.style.display='';
      body.style.display=(v==='full'||post.classList.contains('expanded'))?'':'none';
    }}
  }});
  var emp=document.getElementById('fav-empty');
  if(emp)emp.style.display=(v==='fav'&&n===0)?'':'none';
}}
function toggleAccordion(post){{
  if(document.body.dataset.view!=='toc')return;
  var body=post.querySelector('.post-body');
  var exp=post.classList.toggle('expanded');
  body.style.display=exp?'':'none';
}}
function toggleFav(btn){{
  var id=btn.dataset.id,favs=getFavs();
  if(favs.has(id))favs.delete(id);else favs.add(id);
  saveFavs(favs);
  updateFavUI();
  if(document.body.dataset.view==='fav')applyView();
}}
function updateFavUI(){{
  var favs=getFavs();
  document.querySelectorAll('.fav-btn').forEach(function(btn){{
    var on=favs.has(btn.dataset.id);
    btn.textContent=on?'★':'☆';
    btn.classList.toggle('active',on);
  }});
  var c=favs.size;
  document.getElementById('fav-badge').textContent=c?' ('+c+')':'';
}}
window.addEventListener('DOMContentLoaded',function(){{
  var v=sessionStorage.getItem('phdkim_view')||'toc';
  document.body.dataset.view=v;
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+v).classList.add('active');
  applyView();
  updateFavUI();
}});
</script>
</body>
</html>"""


def write_html(posts: list, output_path: Path = _DEFAULT_HTML_PATH) -> None:
    output_path.write_text(generate_html(posts), encoding="utf-8")
