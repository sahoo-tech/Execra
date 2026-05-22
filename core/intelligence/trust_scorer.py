"""Trust scoring module for the Execra intelligence layer.

This module calculates a weighted reliability score for LLM-generated
instructions by combining LLM confidence, rule validation, and execution
trace matching into a single normalized trust score.

Typical usage example::

    result = calculate_trust_score(
        llm_confidence=0.9,
        rule_validation=True,
        execution_trace_match=0.8,
    )
    print(result["score"], result["level"])
"""

from core.config import settings


def calculate_trust_score(
    llm_confidence: float,
    rule_validation: bool,
    execution_trace_match: float,
) -> dict:
    """Calculate a weighted reliability score for LLM outputs.

    Combines three signals — LLM confidence, rule validation result, and
    execution trace similarity — into a single normalized trust score using
    configurable weights from application settings.

    Args:
        llm_confidence: Confidence score reported by the LLM, must be
            in [0.0, 1.0].
        rule_validation: Whether the output passed the deterministic rule
            validator. ``True`` contributes full weight; ``False``
            contributes zero.
        execution_trace_match: Similarity between the predicted and actual
            execution trace, must be in [0.0, 1.0].

    Returns:
        A dictionary with three keys:

        - ``"score"`` (float): Normalized trust score in [0.0, 1.0].
        - ``"level"`` (str): Qualitative label — one of ``"Trusted"``,
          ``"Moderate"``, ``"Low"``, or ``"Uncertain"``.
        - ``"reasoning"`` (str): Suggested action for the guidance
          dispatcher based on the computed level.

    Raises:
        ValueError: If ``llm_confidence`` or ``execution_trace_match``
            is outside [0.0, 1.0].

    Example::

        result = calculate_trust_score(
            llm_confidence=0.92,
            rule_validation=True,
            execution_trace_match=0.75,
        )
        # result → {"score": 0.88, "level": "Trusted",
        #           "reasoning": "Deliver instruction directly"}
    """
    for name, value in [
        ("llm_confidence", llm_confidence),
        ("execution_trace_match", execution_trace_match),
    ]:
        if not (0.0 <= value <= 1.0):
            raise ValueError(
                f"Input '{name}' must be between 0 and 1. Received: {value}"
            )

    w1 = settings.TRUST_SCORE_W1
    w2 = settings.TRUST_SCORE_W2
    w3 = settings.TRUST_SCORE_W3

    score = (
        w1 * llm_confidence
        + w2 * (1.0 if rule_validation else 0.0)
        + w3 * execution_trace_match
    ) / (w1 + w2 + w3)

    level = ""
    reasoning = ""

    if score >= 0.85:
        level = "Trusted"
        reasoning = "Deliver instruction directly"
    elif 0.65 <= score <= 0.84:
        level = "Moderate"
        reasoning = "Deliver with visible reasoning"
    elif 0.50 <= score <= 0.64:
        level = "Low"
        reasoning = "Flag uncertainty, invite user confirmation"
    else:
        level = "Uncertain"
        reasoning = "Flag + request clarification, do not auto-suggest"

    return {"score": score, "level": level, "reasoning": reasoning}
