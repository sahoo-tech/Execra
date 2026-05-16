from dataclasses import dataclass

from core.physical.task_recognizer import TaskRecognizer


@dataclass
class MockDetection:
    label: str


def test_recognize_cooking_from_detected_objects():
    recognizer = TaskRecognizer()

    task_type = recognizer.recognize(
        [MockDetection("bowl"), MockDetection("tomato")],
        "",
    )

    assert task_type == "cooking"


def test_recognize_hardware_repair_from_detected_objects():
    recognizer = TaskRecognizer()

    task_type = recognizer.recognize(
        [MockDetection("screwdriver"), MockDetection("laptop")],
        "",
    )

    assert task_type == "hardware_repair"


def test_recognize_form_filling_from_ocr_text():
    recognizer = TaskRecognizer()

    task_type = recognizer.recognize(
        [],
        "Name: Priya Sharma\nDate: 2026-05-16\nSignature __________",
    )

    assert task_type == "form_filling"


def test_recognize_document_reading_from_long_ocr_text_without_tools():
    recognizer = TaskRecognizer()
    long_text = " ".join(["policy"] * 101)

    task_type = recognizer.recognize(
        [MockDetection("book")],
        long_text,
    )

    assert task_type == "document_reading"


def test_document_reading_not_returned_when_tools_are_detected():
    recognizer = TaskRecognizer()
    long_text = " ".join(["instruction"] * 120)

    task_type = recognizer.recognize(
        [MockDetection("wire")],
        long_text,
    )

    assert task_type == "hardware_repair"


def test_recognize_unknown_when_no_rule_matches():
    recognizer = TaskRecognizer()

    task_type = recognizer.recognize(
        [MockDetection("chair")],
        "short note",
    )

    assert task_type == "unknown"


def test_get_step_guidance_returns_known_task_steps():
    recognizer = TaskRecognizer()

    steps = recognizer.get_step_guidance("cooking")

    assert steps
    assert all(isinstance(step, str) for step in steps)


def test_get_step_guidance_returns_empty_list_for_unknown_task():
    recognizer = TaskRecognizer()

    assert recognizer.get_step_guidance("unknown") == []
