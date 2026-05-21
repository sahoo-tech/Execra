import pytest

from core.hybrid.action_logger import ActionLogger, ActionRecord


def test_record_action_adds_action_to_history():
    logger = ActionLogger()
    action = ActionRecord(type="click", description="Clicked run button")

    logger.record_action(action)

    assert logger.total_actions() == 1
    assert logger.list_actions() == [action]


def test_undo_last_marks_latest_undoable_action():
    logger = ActionLogger()
    first_action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
        undo_instruction="Restore previous value",
    )
    second_action = ActionRecord(type="view", description="Opened settings")

    logger.record_action(first_action)
    logger.record_action(second_action)

    undone = logger.undo_last()

    assert undone == first_action
    assert first_action.undone is True


def test_double_undo_returns_none_when_no_undoable_action_remains():
    logger = ActionLogger()
    action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
        undo_instruction="Restore previous value",
    )

    logger.record_action(action)

        # Verify that an INSERT INTO command was executed
        insert_calls = [call for call in mock_db.execute.call_args_list if "INSERT INTO" in call[0][0]]
        assert len(insert_calls) == 1
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_replay_session_yields_matching_session_actions_in_order():
    logger = ActionLogger()
    first_action = ActionRecord(type="step", description="First", session_id="session-1")
    second_action = ActionRecord(type="step", description="Second", session_id="session-2")
    third_action = ActionRecord(type="step", description="Third", session_id="session-1")

    logger.record_action(first_action)
    logger.record_action(second_action)
    logger.record_action(third_action)

    replayed_actions = [
        action async for action in logger.replay_session(session_id="session-1")
    ]

    assert replayed_actions == [first_action, third_action]

        # Verify that a DELETE FROM command was executed
        delete_calls = [call for call in mock_db.execute.call_args_list if "DELETE FROM" in call[0][0]]
        assert len(delete_calls) == 1
        assert mock_db.commit.called

@pytest.mark.asyncio
async def test_replay_session_rejects_invalid_speed():
    logger = ActionLogger()

    with pytest.raises(ValueError, match="Replay speed"):
        async for _ in logger.replay_session(speed=0):
            pass
