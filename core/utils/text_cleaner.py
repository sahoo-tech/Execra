import re
import unicodedata

class TextCleaner:
    @staticmethod
    def clean_ocr(text: str) -> str:
        if not text:
            return ""
        text = text.replace('\x00', '')
        text = unicodedata.normalize('NFC', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.rstrip() for line in text.split('\n')]
        lines = [line for line in lines if len(line.strip()) >= 3]
        return '\n'.join(lines)
    
    @staticmethod
    def clean_llm_response(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'```[\w]*\n?', '', text)
        text = re.sub(r'^(Assistant:|AI:)\s*', '', text, flags=re.MULTILINE)
        return text.strip()
    
    @staticmethod
    def extract_code_blocks(text: str) -> list:
        if not text:
            return []
        pattern = r'```[\w]*\n(.*?)```'
        return re.findall(pattern, text, re.DOTALL)
    
    @staticmethod
    def truncate(text: str, max_chars: int = 2000, suffix: str = "...") -> str:
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + suffix
    
    @staticmethod
    def sanitize_for_sql(text: str) -> str:
        if not text:
            return ""
        return text.replace("'", "''") 