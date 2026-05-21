import pytest
from core.utils.text_cleaner import TextCleaner

class TestCleanOcr:
    def test_normal(self):
        text = "Hello\x00 World\n\n\n\nNew paragraph"
        result = TextCleaner.clean_ocr(text)
        assert '\x00' not in result
        assert '\n\n\n' not in result

    def test_short_lines_removed(self):
        text = "Hello World\nab\nValid line here"
        result = TextCleaner.clean_ocr(text)
        assert 'ab' not in result
        assert 'Valid line here' in result
    
    def test_empty_string(self):
        assert TextCleaner.clean_ocr("") == ""
class TestCleanLlmResponse:
    def test_removes_code_fences(self):
        text = "```python\nprint('hello')\n```"
        result = TextCleaner.clean_llm_response(text)
        assert  '```' not in result
    def test_removed_assistant_prefix(self):
        text = "Assistant: Here is the answer"
        result = TextCleaner.clean_llm_response(text)
        assert not result.startswith('Assistant:')
        
    def test_empty_string(self):
        assert TextCleaner.clean_llm_response("") == ""
class TestExtractCodeBlocks:
    def test_single_block(self):
        text = "```python\nprint('hello')\n```"
        result = TextCleaner.extract_code_blocks(text)
        assert len(result) == 1

    def test_multiple_blocks(self):
        text = "```python\ncode1\n```\ntext\n```js\ncode2\n```"
        result = TextCleaner.extract_code_blocks(text)
        assert len(result) == 2

    def test_empty_string(self):
        assert TextCleaner.extract_code_blocks("") == []

class TestTruncate:
    def test_normal(self):
        text = "word " * 500
        result = TextCleaner.truncate(text, max_chars=100)
        assert len(result) <= 103
    def test_short_text(self):
        text = "Short text"
        assert TextCleaner.truncate(text) == text
    def test_empty_string(self):
        assert TextCleaner.truncate("") == ""
class TestSanitizeForSql:
    def test_single_quote(self):
        result = TextCleaner.sanitize_for_sql("O'Brien")
        assert result == "O''Brien"
    def test_no_quotes(self):
        assert TextCleaner.sanitize_for_sql("hello") == "hello"
    def test_empty_string(self):
        assert TextCleaner.sanitize_for_sql("") == ""
