import unittest
from unittest.mock import patch, MagicMock
import numpy as np


from core.physical.depth_estimator import DepthEstimator

class TestDepthEstimator(unittest.TestCase):

    
    @patch('torch.hub.load')
    def test_model_initialization(self, mock_hub_load):
        """Tests if the class initializes without downloading the real AI model"""
        
        
        estimator = DepthEstimator()
        
        
        self.assertTrue(mock_hub_load.called)
        
        
        self.assertIsNotNone(estimator.device)

    @patch('torch.hub.load') 
    def test_get_object_depth_calculation(self, mock_hub_load):
        """Tests if the numpy matrix slicing and mean calculation is mathematically correct"""
        estimator = DepthEstimator()
        
        
        fake_depth_map = np.full((10, 10), 5.0)
        
        
        # Rows 2 to 4, Cols 2 to 4
        fake_depth_map[2:4, 2:4] = 10.0
        
        
        bounding_box = [2, 2, 4, 4]
        
       
        result = estimator.get_object_depth(fake_depth_map, bounding_box)
        
        
        self.assertEqual(result, 10.0)

if __name__ == '__main__':
    unittest.main()