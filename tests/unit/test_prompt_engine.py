from pathlib import Path

import pytest
from jinja2 import UndefinedError

from core.intelligence.prompt_engine import PromptEngine


@pytest.fixture
def prompt_engine():
    return PromptEngine()


def test_render_success(prompt_engine):
    result = prompt_engine.render(
        "step_decomposition.j2",
        {
            "goal": "Build an AI assistant",
            "context_text": "Python project",
            "max_steps": 3,
        },
    )

    assert "Build an AI assistant" in result
    assert "Python project" in result


def test_missing_variable_raises(prompt_engine):
    with pytest.raises(UndefinedError):
        prompt_engine.render(
            "step_decomposition.j2",
            {
                "goal": "Build project",
                # missing context_text
                "max_steps": 3,
            },
        )


def test_render_with_fallback(prompt_engine):
    result = prompt_engine.render_with_fallback(
        "missing_template.j2",
        {
            "name": "Aditya",
        },
        "Hello {{ name }}",
    )

    assert result == "Hello Aditya"


def test_validation_catches_missing_required(tmp_path: Path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    broken_template = template_dir / "broken.j2"

    broken_template.write_text(
        """
        {# required: goal #}

        Goal:
        {{ goal }}

        Context:
        {{ missing_var }}
        """
    )

    engine = PromptEngine(template_dir=str(template_dir))

    with pytest.raises(ValueError):
        engine.render(
            "broken.j2",
            {
                "goal": "Test goal",
            },
        )

def test_consequence_template_render(prompt_engine):
    result = prompt_engine.render(
        "consequence_check.j2",
        {
            "next_action": "Delete database",
            "current_state": "Production environment",
        },
    )

    assert "Delete database" in result
    assert "Production environment" in result

def test_guidance_request_template_render(prompt_engine):
    result = prompt_engine.render(
        "guidance_request.j2",
        {
            "context": "User is clicking a button",
            "screen_text": "Submit Form",
            "trace_summary": "Previous steps...",
        },
    )

    assert "User is clicking a button" in result
    assert "Submit Form" in result
    assert "Previous steps..." in result