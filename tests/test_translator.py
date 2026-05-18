from unittest.mock import MagicMock, patch


def test_translate_text_calls_deepl_with_correct_args():
    mock_result = MagicMock()
    mock_result.text = "中文翻译结果"
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate_text.return_value = mock_result

    with patch("scraper.translator.deepl.Translator", return_value=mock_translator_instance):
        from scraper.translator import translate_text
        result = translate_text("한국어 텍스트", api_key="fake-key")

    assert result == "中文翻译结果"
    mock_translator_instance.translate_text.assert_called_once_with(
        "한국어 텍스트", source_lang="KO", target_lang="ZH"
    )


def test_translate_text_returns_empty_string_for_empty_input():
    from scraper.translator import translate_text
    assert translate_text("", api_key="fake-key") == ""


def test_translate_text_returns_empty_string_for_whitespace_only():
    from scraper.translator import translate_text
    assert translate_text("   \n  ", api_key="fake-key") == ""
