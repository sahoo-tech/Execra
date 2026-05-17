from core.config import settings
from core.telemetry.tracing import get_tracer, SPAN_INTELLIGENCE_TRUST

def calculate_trust_score(llm_confidence: float, rule_validation: bool, execution_trace_match: float) -> dict:
    """
    Calculates a weighted reliability score for LLM outputs.
    Logic remains strictly weighted at 0.5, 0.3, and 0.2.
    """

    for name, value in [("llm_confidence", llm_confidence), ("execution_trace_match", execution_trace_match)]:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"Input '{name}' must be between 0 and 1. Received: {value}")

    with get_tracer("execra.intelligence").start_as_current_span(SPAN_INTELLIGENCE_TRUST) as span:
        w1 = settings.TRUST_SCORE_W1
        w2 = settings.TRUST_SCORE_W2
        w3 = settings.TRUST_SCORE_W3

        score = (w1 * llm_confidence + w2 * (1.0 if rule_validation else 0.0) + w3 * execution_trace_match) / (w1 + w2 + w3)

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

        span.set_attribute("trust.score", score)
        span.set_attribute("trust.level", level)

        return {"score": score, "level": level, "reasoning": reasoning}
