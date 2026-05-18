import deepl


def translate_text(text: str, api_key: str, source: str = "KO", target: str = "ZH") -> str:
    if not text or not text.strip():
        return ""
    client = deepl.Translator(api_key)
    result = client.translate_text(text, source_lang=source, target_lang=target)
    return result.text
