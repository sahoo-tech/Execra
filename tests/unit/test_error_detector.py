from core.digital.error_detector import ErrorDetector


def test_detect_exception():
    detector = ErrorDetector()

    trace = [
        {
            "event_type": "exception",
            "exception": "ZeroDivisionError",
            "line": 10,
        }
    ]

    errors = detector.analyze_trace(trace)

    assert len(errors) == 1
    assert errors[0]["type"] == "UnhandledException"


def test_detect_unexpected_none():
    detector = ErrorDetector()

    trace = [
        {
            "event_type": "return",
            "expected_return_type": "int",
            "return_value": None,
            "line": 20,
        }
    ]

    errors = detector.analyze_trace(trace)

    assert errors[0]["type"] == "UnexpectedNoneReturn"


def test_detect_type_mismatch():
    detector = ErrorDetector()

    trace = [
        {
            "event_type": "return",
            "expected_return_type": "int",
            "return_value": "hello",
            "line": 30,
        }
    ]

    errors = detector.analyze_trace(trace)

    assert errors[0]["type"] == "TypeMismatch"


def test_detect_excessive_recursion():
    detector = ErrorDetector()

    trace = [{"event_type": "call"} for _ in range(501)]

    errors = detector.analyze_trace(trace)

    assert any(error["type"] == "ExcessiveRecursion" for error in errors)


def test_detect_infinite_loop():
    detector = ErrorDetector(loop_threshold=5)

    trace = [
        {
            "event_type": "loop_iteration",
            "loop_id": "loop1",
            "line": 50,
        }
        for _ in range(6)
    ]

    errors = detector.analyze_trace(trace)

    assert any(error["type"] == "PotentialInfiniteLoop" for error in errors)


def test_detect_from_exception():
    detector = ErrorDetector()

    try:
        1 / 0
    except Exception as exc:
        result = detector.detect_from_exception(exc, "traceback info")

    assert result["type"] == "ZeroDivisionError"
