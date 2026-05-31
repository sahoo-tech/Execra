import pytesseract
import numpy as np
from PIL import Image
import cv2


class OCREngine:
    def __init__(self, language="eng"):
        self.language = language

    def validate_frame(self, array: np.ndarray):
        """Validate the input frame before OCR processing."""
        if array is None:
            raise ValueError("This array is not allowed.")

        if not isinstance(array, np.ndarray):
            raise ValueError("Frame must be a numpy ndarray")

        if array.size == 0:
            return False
        else:
            return True

    def convert_to_pil_image(self, array: np.ndarray):
        """Convert a numpy image array to a PIL image."""
        return Image.fromarray(array)

    def extract_physical_text_with_boxes(self, array: np.ndarray):
        """Extract OCR text along with bounding box coordinates."""
        valid = self.validate_frame(array)
        if not valid:
            return []

        gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)

        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        processed = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        pil_image = self.convert_to_pil_image(processed)
        data = pytesseract.image_to_data(
            pil_image,
            lang=self.language,
            output_type=pytesseract.Output.DICT,
            config="--oem 3 --psm 3",
        )

        final = []
        for i in range(len(data["text"])):

            text = data["text"][i].strip()

            if text == "":
                continue
            try:
                conf = float(data["conf"][i])
            except ValueError:
                continue
            if not any(ch.isalnum() for ch in text):
                continue

            if len(text) <= 3 and conf < 80:
                continue
            if conf < 23:
                continue

            if text != "":
                final.append(
                    {
                        "text": text,
                        "box": {
                            "left": data["left"][i],
                            "top": data["top"][i],
                            "height": data["height"][i],
                            "width": data["width"][i],
                        },
                        "conf": conf,
                    }
                )
        return final

    def extract_dig_text(self, array: np.ndarray) -> str:
        """Extract plain text from digitally generated images."""
        valid = self.validate_frame(array)
        if not valid:
            return ""

        gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)

        pil_img = self.convert_to_pil_image(gray)
        return pytesseract.image_to_string(
            pil_img, lang=self.language, config="--oem 3 --psm 6"
        ).strip()
