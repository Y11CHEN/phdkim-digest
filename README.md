# phdkim.net 中文精选周报

自动从韩国博士生社区 [phdkim.net](https://phdkim.net/board) 抓取高赞帖子，翻译成中文，每周发布到静态网页。

## 📖 在线阅读

**👉 [https://y11chen.github.io/phdkim-digest/](https://y11chen.github.io/phdkim-digest/)**

---

## 工作原理

- **每周日 UTC 00:00** 自动运行，抓取点赞数 > 50 的新帖子
- 通过 DeepL API 将韩语标题和正文翻译成中文
- 去重：已收录的帖子不会重复出现
- 生成静态 HTML，通过 GitHub Pages 发布

数据存储在 `data/posts.json`，网站文件在 `docs/index.html`。

---

## 本地运行

**环境要求：** Python 3.12+

```bash
pip install -r requirements.txt
```

**周更脚本（手动触发）：**

```bash
export DEEPL_API_KEY="你的Key"
python scraper/scrape.py
```

**初始化（一次性，抓取历史高赞帖）：**

```bash
export DEEPL_API_KEY="你的Key"
python scraper/bootstrap.py
```

---

## 部署配置

1. Fork 或克隆本仓库到自己的 GitHub
2. 在 Settings → Secrets → Actions 中添加 `DEEPL_API_KEY`（[DeepL 免费注册](https://www.deepl.com/pro-api)，每月 50 万字符免费额度）
3. 在 Settings → Pages 中选择 `main` 分支 `/docs` 目录
4. 运行一次 `bootstrap.py` 初始化数据，推送到仓库
5. 之后每周日自动更新

---

## 仅供个人使用
