# Gemini 翻译替换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace DeepL with Gemini 2.5 Flash as the translation backend, using a domain-specific system prompt to improve accuracy on Korean PhD community terminology.

**Architecture:** Swap `scraper/translator.py` to use `google-generativeai` instead of `deepl`; keep the `translate_text(text, api_key)` function signature unchanged so all callers require zero edits beyond the env-var rename. Update `requirements.txt`, GitHub Actions workflow, and the three scripts that read `DEEPL_API_KEY`.

**Tech Stack:** Python 3.12, google-generativeai SDK, pytest, GitHub Actions.

---

## File Map

| File | Change |
|------|--------|
| `tests/test_translator.py` | Replace deepl mock with genai mock (3 tests, same count) |
| `scraper/translator.py` | Swap deepl import + implementation for google-generativeai |
| `requirements.txt` | `deepl>=1.18.0` → `google-generativeai>=0.8.0` |
| `.github/workflows/weekly.yml` | `DEEPL_API_KEY` → `GEMINI_API_KEY` |
| `scraper/scrape.py` | `DEEPL_API_KEY` → `GEMINI_API_KEY` (one line) |
| `scraper/bootstrap.py` | `DEEPL_API_KEY` → `GEMINI_API_KEY` (one line) |
| `scraper/bulk_import.py` | `DEEPL_API_KEY` → `GEMINI_API_KEY` (one line) |

---

### Task 1: Replace translator core (TDD)

**Files:**
- Modify: `tests/test_translator.py` (full replacement)
- Modify: `scraper/translator.py` (full replacement)
- Modify: `requirements.txt` (one line swap)

- [ ] **Step 1: Write the failing tests**

Replace the entire contents of `tests/test_translator.py` with:

```python
from unittest.mock import MagicMock, patch


def test_translate_text_calls_gemini_with_correct_args():
    mock_response = MagicMock()
    mock_response.text = "中文翻译结果"
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch("scraper.translator.genai.GenerativeModel", return_value=mock_model):
        from scraper.translator import translate_text
        result = translate_text("한국어 텍스트", api_key="fake-key")

    assert result == "中文翻译结果"
    mock_model.generate_content.assert_called_once_with("한국어 텍스트")


def test_translate_text_returns_empty_string_for_empty_input():
    from scraper.translator import translate_text
    assert translate_text("", api_key="fake-key") == ""


def test_translate_text_returns_empty_string_for_whitespace_only():
    from scraper.translator import translate_text
    assert translate_text("   \n  ", api_key="fake-key") == ""
```

- [ ] **Step 2: Run tests to verify the integration test fails**

```
pytest tests/test_translator.py -v
```

Expected: `test_translate_text_calls_gemini_with_correct_args` FAILED (AttributeError — `scraper.translator` has no attribute `genai`); the other two PASS.

- [ ] **Step 3: Replace translator.py**

Replace the entire contents of `scraper/translator.py` with:

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

- [ ] **Step 4: Update requirements.txt**

Replace `deepl>=1.18.0` with `google-generativeai>=0.8.0`. Full file should be:

```
# Python 3.12+
requests>=2.31.0
beautifulsoup4>=4.12.3
google-generativeai>=0.8.0
pytest>=8.1.0
```

- [ ] **Step 5: Install updated dependencies**

```
pip install -r requirements.txt
```

Expected: `google-generativeai` installed, `deepl` left over in the environment (harmless — it's just not in requirements anymore).

- [ ] **Step 6: Run translator tests to verify they pass**

```
pytest tests/test_translator.py -v
```

Expected: 3 PASSED.

- [ ] **Step 7: Run full test suite to catch regressions**

```
pytest tests/ -v
```

Expected: all tests PASSED.

- [ ] **Step 8: Commit**

```bash
git add scraper/translator.py tests/test_translator.py requirements.txt
git commit -m "feat: replace DeepL with Gemini 2.5 Flash for translation"
```

---

### Task 2: Update env var references

**Files:**
- Modify: `.github/workflows/weekly.yml`
- Modify: `scraper/scrape.py`
- Modify: `scraper/bootstrap.py`
- Modify: `scraper/bulk_import.py`

- [ ] **Step 1: Update weekly.yml**

In `.github/workflows/weekly.yml`, find:

```yaml
      - name: Run weekly scraper
        env:
          DEEPL_API_KEY: ${{ secrets.DEEPL_API_KEY }}
        run: python scraper/scrape.py
```

Replace with:

```yaml
      - name: Run weekly scraper
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python scraper/scrape.py
```

- [ ] **Step 2: Update scrape.py**

In `scraper/scrape.py`, find:

```python
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        print("Error: DEEPL_API_KEY environment variable not set.")
```

Replace with:

```python
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
```

- [ ] **Step 3: Update bootstrap.py**

In `scraper/bootstrap.py`, find:

```python
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        print("Error: DEEPL_API_KEY environment variable not set.")
```

Replace with:

```python
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
```

- [ ] **Step 4: Update bulk_import.py**

In `scraper/bulk_import.py`, find:

```python
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        print("Error: DEEPL_API_KEY environment variable not set.")
```

Replace with:

```python
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
```

- [ ] **Step 5: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests PASSED (config changes don't affect tested code paths).

- [ ] **Step 6: Add GEMINI_API_KEY to GitHub Secrets**

Go to: GitHub repo → Settings → Secrets and variables → Actions → New repository secret

- Name: `GEMINI_API_KEY`
- Value: your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

(The old `DEEPL_API_KEY` secret can be left or deleted — it's no longer referenced.)

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/weekly.yml scraper/scrape.py scraper/bootstrap.py scraper/bulk_import.py
git commit -m "chore: rename DEEPL_API_KEY to GEMINI_API_KEY across config and scripts"
```
