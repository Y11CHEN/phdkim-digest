from unittest.mock import MagicMock, patch


def test_translate_text_calls_gemini_with_correct_args():
    mock_response = MagicMock()
    mock_response.text = "中文翻译结果"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("scraper.translator.genai.Client", return_value=mock_client) as mock_client_cls:
        from scraper.translator import translate_text, _SYSTEM
        result = translate_text("한국어 텍스트", api_key="fake-key")

    assert result == "中文翻译结果"
    mock_client_cls.assert_called_once_with(api_key="fake-key")
    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs.kwargs["model"] == "gemini-2.5-flash"
    assert call_kwargs.kwargs["contents"] == "한국어 텍스트"
    assert call_kwargs.kwargs["config"].system_instruction == _SYSTEM


def test_translate_text_returns_empty_string_for_empty_input():
    from scraper.translator import translate_text
    assert translate_text("", api_key="fake-key") == ""


def test_translate_text_returns_empty_string_for_whitespace_only():
    from scraper.translator import translate_text
    assert translate_text("   \n  ", api_key="fake-key") == ""
