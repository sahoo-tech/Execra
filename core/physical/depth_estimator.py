import os
import cv2
import numpy as np
import torch

class DepthEstimator:
    def __init__(self):
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")  
        else:
            self.device = torch.device("cpu")   
            
        print(f"[INFO] Initializing DepthEstimator on device: {self.device}")

        self.model_type = "MiDaS_small"
        self.model = torch.hub.load("intel-isl/MiDaS", self.model_type, trust_repo=True)
        self.model.to(self.device)
        self.model.eval()

        # Loading transformation and configuration
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        self.transform = midas_transforms.small_transform

        self.proximity_threshold = float(os.getenv("PROXIMITY_THRESHOLD", 0.70))

    def estimate_object_depth(self, frame: np.ndarray, bbox: list) -> float:
        """
        Accepts a raw video frame and a single object bounding box coordinates.
        Returns the calculated average relative depth of that object zone.
        """
        if frame is None or len(bbox) != 4:
            return 0.0
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        input_batch = self.transform(rgb_frame).to(self.device)

        with torch.no_grad():  
            prediction = self.model(input_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=frame.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

        depth_map = prediction.cpu().numpy()

        depth_min = depth_map.min()
        depth_max = depth_map.max()
        if depth_max - depth_min > 0:
            depth_map = (depth_map - depth_min) / (depth_max - depth_min)
        else:
            depth_map = np.zeros_like(depth_map)

        x_start = int(bbox[0])
        y_start = int(bbox[1])
        x_end = int(bbox[2])
        y_end = int(bbox[3])

        object_depth_zone = depth_map[y_start:y_end, x_start:x_end]

        if object_depth_zone.size == 0:
            return 0.0
        
        average_depth = float(np.mean(object_depth_zone))
        return average_depth

    def is_dangerously_close(self, average_depth: float) -> bool:
        """
        Compares the calculated average depth against the PROXIMITY_THRESHOLD.
        Returns True if the object violates the safety boundary zone.
        """
        if average_depth >= self.proximity_threshold:
            print(f"[WARNING ALERT] Hazard detected inside critical safety boundary threshold! (Current Depth: {average_depth:.2f})")
            return True
        return False
    