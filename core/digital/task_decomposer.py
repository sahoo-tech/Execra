from __future__ import annotations

import re
from typing import Any


class TaskDecomposer:
    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    async def decompose(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        max_steps: int = 5,
    ) -> list[str]:
        if not goal or not goal.strip():
            return self._fallback_steps("Complete the task", max_steps=max_steps)

        prompt = self._build_decomposition_prompt(
            goal=goal.strip(),
            context=context or {},
            max_steps=max_steps,
        )

        response_text = await self._call_with_retry(prompt)
        steps = self._parse_steps(response_text, max_steps=max_steps)

        if steps:
            return steps

        return self._fallback_steps(goal.strip(), max_steps=max_steps)

    async def suggest_next_step(
        self,
        goal: str,
        completed_steps: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        completed_steps = completed_steps or []

        if self.llm_client is None:
            return self._default_next_step(goal, completed_steps)

        prompt = self._build_next_step_prompt(
            goal=goal.strip(),
            completed_steps=completed_steps,
            context=context or {},
        )

        try:
            response = await self._invoke_llm(prompt)
            suggestion = self._clean_single_step(response)
            if suggestion:
                return suggestion
        except Exception:
            pass

        return self._default_next_step(goal, completed_steps)

    async def _call_with_retry(self, prompt: str) -> str:
        if self.llm_client is None:
            return ""

        for attempt in range(2):
            try:
                return await self._invoke_llm(prompt)
            except Exception:
                if attempt == 1:
                    return ""

        return ""

    async def _invoke_llm(self, prompt: str) -> str:
        if self.llm_client is None:
            return ""

        for method_name in ("generate", "complete", "chat", "ainvoke", "invoke"):
            method = getattr(self.llm_client, method_name, None)
            if callable(method):
                result = method(prompt)
                if hasattr(result, "__await__"):
                    result = await result
                return self._extract_text(result)

        raise AttributeError("LLM client does not expose a supported generation method")

    def _extract_text(self, result: Any) -> str:
        if result is None:
            return ""

        if isinstance(result, str):
            return result.strip()

        if isinstance(result, dict):
            for key in ("text", "content", "response", "output"):
                value = result.get(key)
                if isinstance(value, str):
                    return value.strip()

        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content.strip()

        text = getattr(result, "text", None)
        if isinstance(text, str):
            return text.strip()

        return str(result).strip()

    def _parse_steps(self, text: str, max_steps: int = 5) -> list[str]:
        if not text or not text.strip():
            return []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        steps: list[str] = []

        for line in lines:
            cleaned = re.sub(r"^\s*(?:\d+[\).\-\:]|[-*•])\s*", "", line).strip()
            if cleaned:
                steps.append(cleaned)

        if len(steps) <= 1:
            inline_parts = re.split(r"(?:\s*\d+[\).\:]\s+)", text)
            inline_steps = [part.strip(" -•\n\t") for part in inline_parts if part.strip(" -•\n\t")]
            if len(inline_steps) > 1:
                steps = inline_steps

        deduped: list[str] = []
        seen: set[str] = set()

        for step in steps:
            key = step.lower()
            if key not in seen:
                deduped.append(step)
                seen.add(key)

        return deduped[:max_steps]

    def _clean_single_step(self, text: str) -> str:
        parsed = self._parse_steps(text, max_steps=1)
        if parsed:
            return parsed[0]

        cleaned = re.sub(r"^\s*(?:next step\:?)\s*", "", text.strip(), flags=re.IGNORECASE)
        return cleaned

    def _build_decomposition_prompt(
        self,
        goal: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> str:
        context_text = self._format_context(context)
        return (
            f"You are a task decomposition assistant.\n"
            f"Break the following goal into {max_steps} or fewer clear, practical steps.\n"
            f"Return only a numbered list.\n\n"
            f"Goal: {goal}\n"
            f"Context: {context_text}\n"
        )

    def _build_next_step_prompt(
        self,
        goal: str,
        completed_steps: list[str],
        context: dict[str, Any],
    ) -> str:
        completed_text = "; ".join(completed_steps) if completed_steps else "None"
        context_text = self._format_context(context)
        return (
            "You are a task guidance assistant.\n"
            "Given the goal and completed progress, return only the single best next step.\n\n"
            f"Goal: {goal}\n"
            f"Completed steps: {completed_text}\n"
            f"Context: {context_text}\n"
        )

    def _format_context(self, context: dict[str, Any]) -> str:
        if not context:
            return "None"

        parts: list[str] = []
        for key, value in context.items():
            parts.append(f"{key}={value}")
        return ", ".join(parts)

    def _fallback_steps(self, goal: str, max_steps: int = 5) -> list[str]:
        generic = [
            f"Understand the goal: {goal}",
            "Gather the required information, tools, and constraints",
            "Break the work into smaller actionable parts",
            "Execute the parts one by one and verify progress",
            "Review the result and fix any remaining issues",
        ]
        return generic[:max_steps]

    def _default_next_step(self, goal: str, completed_steps: list[str]) -> str:
        if not completed_steps:
            return f"Start by clarifying the goal and constraints for: {goal}"
        return "Review the latest completed step and continue with the next actionable item"