import google.generativeai as genai

_SYSTEM = (
    "你是专业翻译，专门翻译韩国博士申请社区（phdkim.net）的帖子。"
    "将韩文翻译为简体中文，保留学术术语准确性（如导师、推荐信、录取通知、"
    "科研经历等博士申请相关词汇），语言自然流畅。"
    "只输出翻译结果，不加任何解释或前缀。"
)


def translate_text(text: str, api_key: str) -> str:
    if not text or not text.strip():
        return ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=_SYSTEM)
    return model.generate_content(text).text
