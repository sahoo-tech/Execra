import numpy as np
import torch
import cv2

class DepthEstimator:
    def __init__(self):
        """
        Initializes the MiDaS depth estimation model using torch.hub.
        """
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
       
        self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
        self.model.to(self.device)
        self.model.eval()

        
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        self.transform = midas_transforms.small_transform
        

    def estimate(self, frame: np.ndarray) -> np.ndarray:
        """
        Takes a single BGR camera frame (NumPy array), performs 
        monocular depth estimation, and returns a depth map 
        of the exact same width and height.
        """
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        
        input_batch = self.transform(img).to(self.device)

        
        with torch.no_grad():
            prediction = self.model(input_batch)

           
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        
        return prediction.cpu().numpy()
        

    def get_object_depth(self, depth_map: np.ndarray, bounding_box: list) -> float:
        """
        Takes the generated depth map and a bounding box [x_min, y_min, x_max, y_max].
        Returns the mathematical average (mean) depth value within that bounding box region.
        """
        
        x_min, y_min, x_max, y_max = bounding_box
        
        
        cropped_region = depth_map[y_min:y_max, x_min:x_max]
        
       
        return float(np.mean(cropped_region))
       