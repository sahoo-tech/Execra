import os
from dataclasses import dataclass
from typing import List, Optional, Type, Callable


@dataclass
class EnvSpec:
    key: str
    required: bool
    expected_type: Type
    allowed_values: Optional[List] = None
    validator: Optional[Callable[[str], bool]] = None
    description: str = ""


def _validate_redis_url(value: str) -> bool:
    return value.startswith("redis://")


def _validate_fps(value: str) -> bool:
    try:
        v = int(value)
        return 1 <= v <= 30
    except:
        return False


ENV_SCHEMA: List[EnvSpec] = [
    EnvSpec("LLM_BACKEND", True, str, ["openai", "gemini", "local", "llama"]),
    EnvSpec("OPENAI_API_KEY", False, str),
    EnvSpec("GEMINI_API_KEY", False, str),
    EnvSpec("REDIS_URL", True, str, validator=_validate_redis_url),
    EnvSpec("CAPTURE_FPS", False, int, validator=_validate_fps),
    EnvSpec("LOG_FORMAT", False, str, ["console", "json"]),
    EnvSpec("SANDBOX_MODE", False, str, ["static_only", "sandboxed"]),
]


def validate_env() -> List[str]:
    errors = []
    env = os.environ

    for spec in ENV_SCHEMA:
        value = env.get(spec.key)

        # Required check
        if spec.required and not value:
            errors.append(f"{spec.key} is required but not set")
            continue

        if value is None:
            continue

        # Type check
        if spec.expected_type == int:
            try:
                int(value)
            except ValueError:
                errors.append(f"{spec.key} must be an integer")
                continue

        elif spec.expected_type == str:
            if not isinstance(value, str):
                errors.append(f"{spec.key} must be a string")

        # Allowed values check
        if spec.allowed_values and value not in spec.allowed_values:
            errors.append(
                f"{spec.key} must be one of {spec.allowed_values}, got '{value}'"
            )

        # Custom validator
        if spec.validator and not spec.validator(value):
            errors.append(f"{spec.key} has invalid value '{value}'")

    # Conditional validation
    backend = env.get("LLM_BACKEND")

    if backend == "openai" and not env.get("OPENAI_API_KEY"):
        errors.append("OPENAI_API_KEY is required when LLM_BACKEND=openai")

    if backend == "gemini" and not env.get("GEMINI_API_KEY"):
        errors.append("GEMINI_API_KEY is required when LLM_BACKEND=gemini")

    return errors


def assert_env():
    errors = validate_env()
    if errors:
        formatted = "\n".join(f"- {err}" for err in errors)
        raise EnvironmentError(f"Environment validation failed:\n{formatted}")