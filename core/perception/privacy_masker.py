import re
from typing import List, Tuple

import cv2
import numpy as np

from core.config import settings


class PrivacyMasker:
    """
    A core utility for sanitizing multimodal data (images and text)
    before it reaches the intelligence layer or cloud APIs.
    """

    @staticmethod
    def apply_geometric_mask(
        image: np.ndarray, regions: List[Tuple[int, int, int, int]] = None
    ) -> np.ndarray:
        """
        Blacks out specific rectangular regions of the image.

        Args:
            image: The source frame (numpy array).
            regions: List of (x1, y1, x2, y2) coordinates.

        Returns:
            np.ndarray: The masked image.
        """
        if not settings.PRIVACY_MASKING_ENABLED:
            return image

        masked_image = image.copy()
        target_regions = (
            regions if regions is not None else settings.MASKED_REGIONS
        )

        for x1, y1, x2, y2 in target_regions:
            # Ensure coordinates are within image boundaries
            h, w = image.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)

            if x1 < x2 and y1 < y2:
                # Black out the region
                cv2.rectangle(masked_image, (x1, y1), (x2, y2), (0, 0, 0), -1)

        return masked_image

    @staticmethod
    def redact_text(text: str, extra_patterns: List[str] = None) -> str:
        """
        Redacts sensitive patterns (emails, credit cards, etc.) from text.

        Args:
            text: The raw text string.
            extra_patterns: Optional additional regex patterns.

        Returns:
            str: The redacted text.
        """
        if not settings.PRIVACY_MASKING_ENABLED:
            return text

        redacted_text = text
        all_patterns = settings.SENSITIVE_PATTERNS + (extra_patterns or [])

        for pattern in all_patterns:
            redacted_text = re.sub(pattern, "[REDACTED]", redacted_text)

        return redacted_text

    @staticmethod
    def blur_regions(
        image: np.ndarray,
        regions: List[Tuple[int, int, int, int]],
        blur_factor: int = 15,
    ) -> np.ndarray:
        """
        Applies a Gaussian blur to specific regions of the image.

        Args:
            image: The source frame.
            regions: List of (x1, y1, x2, y2) to blur.
            blur_factor: Intensity of the blur (must be odd).

        Returns:
            np.ndarray: The partially blurred image.
        """
        if not settings.PRIVACY_MASKING_ENABLED or not regions:
            return image

        blurred_image = image.copy()
        # Blur kernel size must be odd
        ksize = blur_factor if blur_factor % 2 != 0 else blur_factor + 1

        for x1, y1, x2, y2 in regions:
            h, w = image.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)

            if x1 < x2 and y1 < y2:
                roi = blurred_image[y1:y2, x1:x2]
                roi = cv2.GaussianBlur(roi, (ksize, ksize), 0)
                blurred_image[y1:y2, x1:x2] = roi

        return blurred_image
