from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateNotFound,
    TemplateSyntaxError,
    UndefinedError,
    meta,
)


class PromptEngine:
    """
    Centralized Jinja2 prompt rendering engine.

    Features:
    - Template rendering
    - Strict variable enforcement
    - Required variable validation
    - Fallback rendering
    - Template syntax validation
    """

    REQUIRED_PATTERN = re.compile(
        r"\{#\s*required:\s*(.*?)\s*#\}",
        re.IGNORECASE,
    )

    def __init__(
        self,
        template_dir: str = "prompts/templates",
    ) -> None:
        self.template_path = Path(template_dir)

        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Prompt template directory not found: {template_dir}"
            )

        self.environment = Environment(
            loader=FileSystemLoader(str(self.template_path)),
            undefined=StrictUndefined,
            auto_reload=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """
        Render a template using validated context.
        """
        try:
            loader = self.environment.loader

            if loader is None:
                raise ValueError("Template loader is not configured")

            source, _, _ = loader.get_source(
                self.environment,
                template_name,
            )
            self._validate_template(
                template_name=template_name,
                source=source,
                context=context,
            )

            template = self.environment.get_template(template_name)

            return template.render(**context).strip()

        except TemplateNotFound as exc:
            raise TemplateNotFound(
                f"Template '{template_name}' not found"
            ) from exc

        except TemplateSyntaxError as exc:
            raise TemplateSyntaxError(
                message=f"Syntax error in template '{template_name}': {exc.message}",
                lineno=exc.lineno,
                name=exc.name,
                filename=exc.filename,
            ) from exc

        except UndefinedError:
            raise

    def render_with_fallback(
        self,
        template_name: str,
        context: dict[str, Any],
        fallback_template: str,
    ) -> str:
        """
        Render template with fallback raw template string.
        """
        try:
            return self.render(template_name, context)

        except TemplateNotFound:
            fallback = self.environment.from_string(fallback_template)
            return fallback.render(**context).strip()

    def _validate_template(
        self,
        template_name: str,
        source: str,
        context: dict[str, Any],
    ) -> None:
        """
        Validate required variables and template consistency.
        """
        required_vars = self._extract_required_variables(source)

        missing_context = required_vars - set(context.keys())

        if missing_context:
            raise UndefinedError(
                f"Missing required variables for "
                f"'{template_name}': {sorted(missing_context)}"
            )

        parsed_content = self.environment.parse(source)

        undeclared_vars = meta.find_undeclared_variables(parsed_content)

        missing_required_declarations = undeclared_vars - required_vars

        ignored = {
            "loop",
        }

        missing_required_declarations -= ignored

        if missing_required_declarations:
            raise ValueError(
                f"Template '{template_name}' uses undeclared variables: "
                f"{sorted(missing_required_declarations)}"
            )

    def _extract_required_variables(
        self,
        source: str,
    ) -> set[str]:
        """
        Extract required variables from template metadata comment.

        Example:
        {# required: goal, context_text, max_steps #}
        """
        match = self.REQUIRED_PATTERN.search(source)

        if not match:
            return set()

        raw = match.group(1)

        return {
            item.strip()
            for item in raw.split(",")
            if item.strip()
        }