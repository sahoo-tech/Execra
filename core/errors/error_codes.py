from enum import Enum


class ErrorCode(Enum):
    # General Errors
    UNKNOWN_ERROR = "E000"
    INVALID_INPUT = "E001"

    # LLM Errors
    LLM_TIMEOUT = "E002"
    LLM_RESPONSE_ERROR = "E003"

    # OCR Errors
    OCR_FAILURE = "E004"

    # System Errors
    SCREEN_CAPTURE_FAILED = "E005"
    FILE_NOT_FOUND = "E006"

    # API Errors
    API_REQUEST_FAILED = "E007"