from core.intelligence.trace_anomaly_detector import (
    TraceFeatureExtractor,
    TraceAnomalyDetector
)

normal_trace = [
    {
        "function": "run",
        "line": 10,
        "event": "call",
        "depth": 1,
        "exception": False
    }
] * 20

anomalous_trace = [
    {
        "function": "recursive",
        "line": 99,
        "event": "call",
        "depth": 50,
        "exception": True
    }
] * 300


def test_feature_extraction():
    features = TraceFeatureExtractor.extract(normal_trace)

    assert len(features) == 6


def test_model_training_and_prediction():
    detector = TraceAnomalyDetector()

    detector.fit([normal_trace])

    result, score = detector.predict(anomalous_trace)

    assert isinstance(result, bool)
    assert isinstance(score, float)
