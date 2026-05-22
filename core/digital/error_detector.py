class ErrorDetector:
    def __init__(self, loop_threshold: int = 1000):
        self.loop_threshold = loop_threshold

    def analyze_trace(self, trace_events: list[dict]) -> list[dict]:
        errors = []
        call_depth = 0
        max_depth = 0
        loop_counts = {}

        for event in trace_events:
            event_type = event.get("event_type")

            if event_type == "exception":
                errors.append(
                    {
                        "type": "UnhandledException",
                        "description": event.get(
                            "exception", "Unhandled exception occurred"
                        ),
                        "line": event.get("line"),
                        "severity": "high",
                    }
                )

            if event_type == "call":
                call_depth += 1
                max_depth = max(max_depth, call_depth)

            elif event_type == "return":
                call_depth = max(0, call_depth - 1)

                expected_type = event.get("expected_return_type")
                return_value = event.get("return_value")

                if expected_type and expected_type != "None" and return_value is None:
                    errors.append(
                        {
                            "type": "UnexpectedNoneReturn",
                            "description": f"Function returned None but expected {expected_type}",
                            "line": event.get("line"),
                            "severity": "medium",
                        }
                    )

                if expected_type and return_value is not None:
                    if type(return_value).__name__ != expected_type:
                        errors.append(
                            {
                                "type": "TypeMismatch",
                                "description": (
                                    f"Expected return type {expected_type}, "
                                    f"got {type(return_value).__name__}"
                                ),
                                "line": event.get("line"),
                                "severity": "medium",
                            }
                        )

            if event_type == "loop_iteration":
                loop_id = event.get("loop_id", "unknown")
                loop_counts[loop_id] = loop_counts.get(loop_id, 0) + 1

                if loop_counts[loop_id] > self.loop_threshold:
                    errors.append(
                        {
                            "type": "PotentialInfiniteLoop",
                            "description": f"Loop exceeded {self.loop_threshold} iterations",
                            "line": event.get("line"),
                            "severity": "high",
                        }
                    )

        if max_depth > 500:
            errors.append(
                {
                    "type": "ExcessiveRecursion",
                    "description": f"Recursion depth exceeded limit: {max_depth}",
                    "line": None,
                    "severity": "high",
                }
            )

        return errors

    def detect_from_exception(self, exc: Exception, traceback_str: str) -> dict:
        return {
            "type": type(exc).__name__,
            "description": str(exc),
            "traceback": traceback_str,
            "severity": "high",
        }
