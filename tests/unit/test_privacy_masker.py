import numpy as np

from core.config import settings
from core.perception.privacy_masker import PrivacyMasker


class TestPrivacyMasker:
    """
    Unit tests for the PrivacyMasker utility.
    """

    def test_redact_text_email(self):
        """Should redact email addresses."""
        raw_text = "Contact me at test@example.com for more info."
        expected = "Contact me at [REDACTED] for more info."
        assert PrivacyMasker.redact_text(raw_text) == expected

    def test_redact_text_credit_card(self):
        """Should redact credit card numbers."""
        raw_text = "My card number is 1234-5678-9012-3456."
        expected = "My card number is [REDACTED]."
        assert PrivacyMasker.redact_text(raw_text) == expected

    def test_redact_text_disabled(self):
        """Should not redact if masking is disabled."""
        settings.PRIVACY_MASKING_ENABLED = False
        raw_text = "test@example.com"
        assert PrivacyMasker.redact_text(raw_text) == raw_text
        settings.PRIVACY_MASKING_ENABLED = True  # Reset

    def test_apply_geometric_mask(self):
        """Should black out a region of the image."""
        # Create a white image
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        regions = [(10, 10, 50, 50)]

        masked = PrivacyMasker.apply_geometric_mask(image, regions)

        # Check that the masked region is black (0, 0, 0)
        assert np.all(masked[10:50, 10:50] == 0)
        # Check that other regions are still white
        assert np.all(masked[60:90, 60:90] == 255)

    def test_blur_regions(self):
        """Should apply blur to a region."""
        # Create a high-contrast pattern (half white, half black)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[0:50, 0:100] = 255  # Top half white
        # Blur across the edge
        regions = [(0, 40, 100, 60)]

        blurred = PrivacyMasker.blur_regions(image, regions, blur_factor=21)

        # The blurred edge should contain intermediate values
        roi = blurred[40:60, :]
        assert not np.all((roi == 0) | (roi == 255))
        # Top region (far from edge) should still be 255
        assert np.all(blurred[0:10, :] == 255)
        # Bottom region should still be 0
        assert np.all(blurred[90:100, :] == 0)
