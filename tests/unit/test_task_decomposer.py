import pytest
from unittest.mock import AsyncMock

from core.digital.task_decomposer import TaskDecomposer


@pytest.mark.asyncio
async def test_decompose_returns_parsed_numbered_steps():
    client = type("MockClient", (), {})()
    client.generate = AsyncMock(return_value="1. Open the file\n2. Read the code\n3. Fix the bug")

    decomposer = TaskDecomposer(llm_client=client)
    result = await decomposer.decompose("Fix the bug")

    assert result == ["Open the file", "Read the code", "Fix the bug"]


@pytest.mark.asyncio
async def test_decompose_retries_once_then_succeeds():
    client = type("MockClient", (), {})()
    client.generate = AsyncMock(side_effect=[RuntimeError("temporary"), "1. Step A\n2. Step B"])

    decomposer = TaskDecomposer(llm_client=client)
    result = await decomposer.decompose("Do something")

    assert result == ["Step A", "Step B"]
    assert client.generate.await_count == 2


@pytest.mark.asyncio
async def test_decompose_falls_back_after_two_failures():
    client = type("MockClient", (), {})()
    client.generate = AsyncMock(side_effect=RuntimeError("boom"))

    decomposer = TaskDecomposer(llm_client=client)
    result = await decomposer.decompose("Ship feature")

    assert len(result) == 5
    assert "Understand the goal: Ship feature" == result[0]
    assert client.generate.await_count == 2


@pytest.mark.asyncio
async def test_decompose_falls_back_when_client_missing():
    decomposer = TaskDecomposer(llm_client=None)

    result = await decomposer.decompose("Write docs")

    assert len(result) == 5
    assert result[0] == "Understand the goal: Write docs"


@pytest.mark.asyncio
async def test_suggest_next_step_uses_llm_response():
    client = type("MockClient", (), {})()
    client.generate = AsyncMock(return_value="1. Run the unit tests")

    decomposer = TaskDecomposer(llm_client=client)
    result = await decomposer.suggest_next_step(
        goal="Finish the PR",
        completed_steps=["Implemented the module"],
    )

    assert result == "Run the unit tests"


@pytest.mark.asyncio
async def test_suggest_next_step_falls_back_on_error():
    client = type("MockClient", (), {})()
    client.generate = AsyncMock(side_effect=RuntimeError("failure"))

    decomposer = TaskDecomposer(llm_client=client)
    result = await decomposer.suggest_next_step(
        goal="Finish the PR",
        completed_steps=["Implemented the module"],
    )

    assert result == "Review the latest completed step and continue with the next actionable item"


def test_parse_steps_handles_bullets_and_duplicates():
    decomposer = TaskDecomposer()

    text = "- Check logs\n- Check logs\n- Restart service"
    result = decomposer._parse_steps(text)

    assert result == ["Check logs", "Restart service"]


def test_parse_steps_handles_inline_numbered_text():
    decomposer = TaskDecomposer()

    text = "1. Install dependencies 2. Run tests 3. Commit changes"
    result = decomposer._parse_steps(text)

    assert result == ["Install dependencies", "Run tests", "Commit changes"]