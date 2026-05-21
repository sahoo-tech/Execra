import unittest

from core.intelligence.trust_scorer import calculate_trust_score


class TestTrustScore(unittest.TestCase):

    def setUp(self):
        self.inputs = {
            "valid": {
                "llm_confidence": 0.9,
                "rule_validation": True,
                "execution_trace_match": 0.8
            },

            "moderate": {
                "llm_confidence": 0.7,
                "rule_validation": True,
                "execution_trace_match": 0.6
            },

            "low": {
                "llm_confidence": 0.6,
                "rule_validation": False,
                "execution_trace_match": 1
            },

            "uncertain": {
                "llm_confidence": 0.2,
                "rule_validation": False,
                "execution_trace_match": 0.1
            },

            "high_invalid": {
                "llm_confidence": 1.5,
                "rule_validation": True,
                "execution_trace_match": 0.5
            },

            "low_invalid": {
                "llm_confidence": 0.5,
                "rule_validation": True,
                "execution_trace_match": -1
            }
        }

    def test_trusted_score(self):

        result = calculate_trust_score(**self.inputs["valid"])

        self.assertEqual(result["level"], "Trusted")
        self.assertGreaterEqual(result["score"], 0.85)
        self.assertEqual(
            result["reasoning"],
            "Deliver instruction directly"
        )

    def test_moderate_score(self):

        result = calculate_trust_score(**self.inputs["moderate"])

        self.assertEqual(result["level"], "Moderate")
        self.assertTrue(0.65 <= result["score"] <= 0.84)
        self.assertEqual(
            result["reasoning"],
            "Deliver with visible reasoning"
        )

    def test_low_score(self):

        result = calculate_trust_score(**self.inputs["low"])

        self.assertEqual(result["level"], "Low")
        self.assertTrue(0.50 <= result["score"] <= 0.64)
        self.assertEqual(
            result["reasoning"],
            "Flag uncertainty, invite user confirmation"
        )

    def test_uncertain_score(self):

        result = calculate_trust_score(**self.inputs["uncertain"])

        self.assertEqual(result["level"], "Uncertain")
        self.assertLess(result["score"], 0.50)
        self.assertEqual(
            result["reasoning"],
            "Flag + request clarification, do not auto-suggest"
        )

    def test_invalid_high_input(self):

        with self.assertRaises(ValueError):
            calculate_trust_score(**self.inputs["high_invalid"])

    def test_invalid_low_input(self):

        with self.assertRaises(ValueError):
            calculate_trust_score(**self.inputs["low_invalid"])


if __name__ == "__main__":
    unittest.main()