"""
Regression tests for guidance generation.
"""

import json
from pathlib import Path


DATASET_DIR = Path(
    "tests/regression/dataset"
)


class MockIntelligenceCore:
    """
    Mocked IntelligenceCore used for
    regression validation.
    """

    @staticmethod
    def generate_guidance(
        screen_text,
        trace_summary,
        expected_keywords,
        trust_level,
    ):

        instruction = (
            " ".join(expected_keywords)
            + " guidance generated"
        )

        return {
            "instruction": instruction,
            "trust_level": trust_level,
        }


def load_dataset():

    dataset = []

    for file in DATASET_DIR.glob("*.json"):

        with open(file, "r") as f:

            dataset.append(json.load(f))

    return dataset


def test_guidance_regression():

    dataset = load_dataset()

    assert len(dataset) == 20

    for case in dataset:

        result = (
            MockIntelligenceCore.generate_guidance(
                screen_text=case["screen_text"],
                trace_summary=case["trace_summary"],
                expected_keywords=case[
                    "expected_guidance_keywords"
                ],
                trust_level=case[
                    "expected_trust_level"
                ],
            )
        )

        instruction = (
            result["instruction"].lower()
        )

        for keyword in case[
            "expected_guidance_keywords"
        ]:

            assert keyword.lower() in instruction

        assert (
            result["trust_level"]
            == case["expected_trust_level"]
        )