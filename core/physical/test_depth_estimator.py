import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import torch
from core.physical.depth_estimator import DepthEstimator

class TestDepthEstimator(unittest.TestCase):

    @patch('torch.hub.load')
    def test_depth_and_alert_system(self, mock_hub_load):
        fake_model = MagicMock()
        
        fake_model.return_value = torch.tensor(np.full((1, 480, 640), 5.0))
        mock_hub_load.return_value = fake_model

        estimator = DepthEstimator()

        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_bbox = [10, 10, 50, 50]
        calculated_depth = estimator.estimate_object_depth(fake_frame, test_bbox)

        self.assertEqual(calculated_depth, 0.0)
        self.assertFalse(estimator.is_dangerously_close(calculated_depth))
        self.assertTrue(estimator.is_dangerously_close(1.0))