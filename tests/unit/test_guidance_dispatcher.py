import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from core.models import GuidanceInstruction
from core.hybrid.guidance_dispatcher import GuidanceDispatcher


@pytest.fixture(autouse=True)
def no_suppression():
    """Bypass alert suppressor so all dispatches reach channels in tests."""
    with patch(
        "core.hybrid.guidance_dispatcher.alert_suppressor.should_suppress",
        return_value=False,
    ):
        yield


@pytest.fixture
def instruction():
    return GuidanceInstruction(
        instruction="Press Ctrl+S to save.",
        confidence=0.95,
        source=["llm"],
        reasoning="User needs to save work.",
        mode="expert",
        step=1,
        total_steps=5,
        generated_at=datetime.now(timezone.utc),
    )


def test_register_channel():
    dispatcher = GuidanceDispatcher()
    mock_channel = Mock()
    dispatcher.register_channel(mock_channel)
    assert mock_channel in dispatcher._channels


def test_dispatch_calls_registered_channels(instruction):
    dispatcher = GuidanceDispatcher()
    channel1 = Mock()
    channel2 = Mock()
    dispatcher.register_channel(channel1)
    dispatcher.register_channel(channel2)

    dispatcher.dispatch(instruction)

    channel1.assert_called_once_with(instruction)
    channel2.assert_called_once_with(instruction)


def test_dispatch_continues_on_channel_error(instruction):
    dispatcher = GuidanceDispatcher()
    bad_channel = Mock(side_effect=Exception("Failed"))
    good_channel = Mock()

    dispatcher.register_channel(bad_channel)
    dispatcher.register_channel(good_channel)

    # Should not raise exception despite the bad channel failing
    dispatcher.dispatch(instruction)

    bad_channel.assert_called_once_with(instruction)
    good_channel.assert_called_once_with(instruction)


def test_dispatch_error_alert():
    dispatcher = GuidanceDispatcher()
    mock_channel = Mock()
    dispatcher.register_channel(mock_channel)

    dispatcher.dispatch_error_alert(
        message="Failed to connect to camera", severity="critical", confidence=1.0
    )

    mock_channel.assert_called_once()
    called_instruction = mock_channel.call_args[0][0]

    assert called_instruction.instruction == "[CRITICAL] Failed to connect to camera"
    assert called_instruction.confidence == 1.0
    assert called_instruction.source == ["system"]
    assert called_instruction.mode == "safe"
    assert called_instruction.step == 0


@patch("core.hybrid.guidance_dispatcher.notification.notify")
def test_os_notification_channel(mock_notify, instruction):
    GuidanceDispatcher(enable_os_notifications=True)

    # Call the static method directly to bypass the try/except wrapper in dispatch
    GuidanceDispatcher._os_notification_channel(instruction)

    mock_notify.assert_called_once_with(
        title=f"Execra Guidance - Step {instruction.step}",
        message=instruction.instruction,
        app_name="Execra",
        timeout=10,
    )
