# Gemini 翻译替换设计文档

## 目标

将翻译后端从 DeepL 替换为 Gemini 2.5 Flash，解决博士申请专业术语翻译不准确的问题。通过 system prompt 为模型提供领域上下文，使翻译质量超过 DeepL 的统计翻译。

## 方案

**Gemini 2.5 Flash + 学术上下文 system prompt**

- 模型：`gemini-2.5-flash`（免费额度 1500 requests/天，远超每周一次的用量）
- 函数签名 `translate_text(text, api_key)` 保持不变，调用方零改动

## 改动范围

| 文件 | 改动内容 |
|------|---------|
| `scraper/translator.py` | 换掉 deepl，接入 google-generativeai，加 system prompt |
| `requirements.txt` | `deepl>=1.18.0` → `google-generativeai>=0.8.0` |
| `.github/workflows/weekly.yml` | 环境变量 `DEEPL_API_KEY` → `GEMINI_API_KEY` |
| `scraper/scrape.py` | 读取的 env 变量名更新（一行） |
| `scraper/bootstrap.py` | 读取的 env 变量名更新（一行） |
| `scraper/bulk_import.py` | 读取的 env 变量名更新（一行） |
| `tests/test_translator.py` | mock 目标从 deepl.Translator 改为 genai.GenerativeModel |

`fetcher.py`、`storage.py`、`html_gen.py` 及所有其他文件不受影响。

## 注意事项

`translate_text` 签名保留 `source`/`target` 参数以保持向后兼容，但 Gemini 实现中不会使用这两个参数——翻译方向由 system prompt 固定为韩文→简体中文。所有调用方本来就使用默认值，不受影响。

## translator.py 实现

```python
import google.generativeai as genai

_SYSTEM = (
    "你是专业翻译，专门翻译韩国博士申请社区（phdkim.net）的帖子。"
    "将韩文翻译为简体中文，保留学术术语准确性（如导师、推荐信、录取通知、"
    "科研经历等博士申请相关词汇），语言自然流畅。"
    "只输出翻译结果，不加任何解释或前缀。"
)


def translate_text(text: str, api_key: str, source: str = "KO", target: str = "ZH") -> str:
    if not text or not text.strip():
        return ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=_SYSTEM)
    return model.generate_content(text).text
```

## 测试策略

保留现有 3 个测试，只换 mock 目标：

- `test_translate_text_calls_gemini_with_correct_args` — mock `genai.GenerativeModel`，验证 `generate_content` 被调用且返回值正确
- `test_translate_text_returns_empty_string_for_empty_input` — 不变
- `test_translate_text_returns_empty_string_for_whitespace_only` — 不变

## GitHub Actions 配置

需在 GitHub 仓库 Settings → Secrets 中：
1. 添加 `GEMINI_API_KEY`（从 Google AI Studio 获取）
2. 删除 `DEEPL_API_KEY`（可选，不影响运行）

## 不在范围内

- 不保留 DeepL 作为备用（Gemini 失败时行为与现在一致：跳过该帖）
- 不区分标题/正文使用不同 prompt
- 不添加重试逻辑
