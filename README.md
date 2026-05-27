# phdkim.net 中文精选周报

自动从韩国博士生社区 [phdkim.net](https://phdkim.net/board) 抓取高赞帖子，翻译成中文，每周发布到静态网页。

## 📖 在线阅读

**👉 [https://y11chen.github.io/phdkim-digest/](https://y11chen.github.io/phdkim-digest/)**

---

## 工作原理

- **每周日 UTC 00:00** 自动运行，抓取点赞数 ≥ 20 的新帖子
- 通过 Gemini API（gemini-2.5-flash）将韩语标题和正文翻译成中文（含博士申请领域专业术语优化）
- 去重：已收录的帖子不会重复出现
- 生成静态 HTML，通过 GitHub Pages 发布
- **限速保护**：每次 API 调用间隔 13 秒，符合免费版 5 次/分钟的限制
- **容错处理**：若当周新帖超出每日配额（20 次/天），超出部分跳过而非崩溃，下次运行时重试

数据存储在 `data/posts.json`，网站文件在 `docs/index.html`。

---

## 本地运行

**环境要求：** Python 3.12+

```bash
pip install -r requirements.txt
```

**周更脚本（手动触发）：**

```bash
export GEMINI_API_KEY="你的Key"
python scraper/scrape.py
```

**初始化（一次性，抓取热门帖快照中赞数 ≥ 150 的帖子）：**

```bash
export GEMINI_API_KEY="你的Key"
python scraper/bootstrap.py
```

**历史全量抓取（从平台创立至今，赞数 ≥ 100，断点续跑）：**

```bash
export GEMINI_API_KEY="你的Key"
python scraper/retranslate.py
```

> 扫描精选板块所有分页直到空页为止，每帖翻译完成后立即保存，中断后重新运行会自动跳过已入库的帖子。

**批量导入备选（同上，每 5 页保存一次检查点）：**

```bash
export GEMINI_API_KEY="你的Key"
python scraper/bulk_import.py
```

---

## 部署配置

1. Fork 或克隆本仓库到自己的 GitHub
2. 在 Settings → Secrets → Actions 中添加 `GEMINI_API_KEY`（[Google AI Studio](https://aistudio.google.com/app/apikey) 免费申请）
3. 在 Settings → Pages 中选择 `main` 分支 `/docs` 目录
4. 运行一次 `bootstrap.py` 初始化数据，推送到仓库
5. 之后每周日自动更新

---

## 仅供个人使用
