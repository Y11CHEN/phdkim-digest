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
