def test_sanity():
    """
    A simple sanity test to verify that the test runner is working.
    """
    assert 1 + 1 == 2

def test_mock_settings(mock_settings):
    """
    Verify that the mock_settings fixture is working.
    """
    assert mock_settings.LLM_BACKEND == "test-model"
    assert mock_settings.API_PORT == 9999
