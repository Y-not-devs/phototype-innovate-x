"""
YOLO Object Detection Inference Wrapper
Detects signatures, stamps, and QR codes in document images
"""
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("Ultralytics not installed. Install with: pip install ultralytics")

from .config import (
    WEIGHTS_PATH,
    DETECTION_CLASSES,
    MODEL_CONFIG,
    CLASS_THRESHOLDS,
    POST_PROCESS_CONFIG
)

logger = logging.getLogger(__name__)


class ObjectDetector:
    """
    Wrapper for YOLO model to detect document elements
    (signatures, stamps, QR codes)
    """
    
    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        confidence_threshold: Optional[float] = None,
        nms_threshold: Optional[float] = None,
        device: Optional[str] = None
    ):
        """
        Initialize object detector
        
        Args:
            model_path: Path to YOLO weights file (e.g., best.pt)
            confidence_threshold: Override default confidence threshold
            nms_threshold: Override default NMS threshold
            device: 'cuda' or 'cpu'
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics package is required. "
                "Install with: pip install ultralytics"
            )
        
        self.model_path = Path(model_path) if model_path else WEIGHTS_PATH
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at {self.model_path}. "
                "Please train a model or download pretrained weights."
            )
        
        # Load YOLO model
        logger.info(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(str(self.model_path))
        
        # Configuration
        self.conf_threshold = confidence_threshold or MODEL_CONFIG["confidence_threshold"]
        self.nms_threshold = nms_threshold or MODEL_CONFIG["nms_threshold"]
        self.device = device or MODEL_CONFIG["device"]
        self.imgsz = MODEL_CONFIG["imgsz"]
        
        logger.info(
            f"Detector initialized - Device: {self.device}, "
            f"Confidence: {self.conf_threshold}, NMS: {self.nms_threshold}"
        )
    
    def detect(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        page_number: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Detect objects in a single image
        
        Args:
            image: Image as file path, numpy array, or PIL Image
            page_number: Page number for multi-page documents
        
        Returns:
            List of detections in format:
            [
                {
                    "page": 0,
                    "label": "signature",
                    "bbox": [x1, y1, x2, y2],  # xyxy format
                    "confidence": 0.85
                },
                ...
            ]
        """
        # Run inference
        results = self.model.predict(
            source=image,
            conf=self.conf_threshold,
            iou=self.nms_threshold,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False
        )
        
        detections = []
        
        # Process results
        for result in results:
            boxes = result.boxes
            
            if boxes is None or len(boxes) == 0:
                continue
            
            # Extract detection data
            xyxy = boxes.xyxy.cpu().numpy()  # Bounding boxes
            confidences = boxes.conf.cpu().numpy()  # Confidence scores
            class_ids = boxes.cls.cpu().numpy().astype(int)  # Class IDs
            
            # Convert to required format
            for i in range(len(boxes)):
                class_id = class_ids[i]
                label = DETECTION_CLASSES.get(class_id, f"class_{class_id}")
                bbox = xyxy[i].tolist()  # [x1, y1, x2, y2]
                confidence = float(confidences[i])
                
                # Apply class-specific threshold if configured
                class_threshold = CLASS_THRESHOLDS.get(label, self.conf_threshold)
                if confidence < class_threshold:
                    continue
                
                # Apply post-processing filters
                if not self._is_valid_detection(bbox, result.orig_shape):
                    continue
                
                detection = {
                    "page": page_number,
                    "label": label,
                    "bbox": bbox,
                    "confidence": round(confidence, 4)
                }
                detections.append(detection)
        
        logger.info(f"Found {len(detections)} objects on page {page_number}")
        return detections
    
    def detect_batch(
        self,
        images: List[Union[str, Path, np.ndarray, Image.Image]],
        page_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect objects in multiple images (batch processing)
        
        Args:
            images: List of images
            page_numbers: Corresponding page numbers (optional)
        
        Returns:
            Flattened list of all detections from all images
        """
        if page_numbers is None:
            page_numbers = list(range(len(images)))
        
        all_detections = []
        
        for image, page_num in zip(images, page_numbers):
            detections = self.detect(image, page_num)
            all_detections.extend(detections)
        
        return all_detections
    
    def _is_valid_detection(self, bbox: List[float], image_shape: tuple) -> bool:
        """
        Apply post-processing filters to detection
        
        Args:
            bbox: Bounding box [x1, y1, x2, y2]
            image_shape: Original image shape (height, width)
        
        Returns:
            True if detection passes filters
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        # Check minimum area
        area = width * height
        if area < POST_PROCESS_CONFIG["min_bbox_area"]:
            return False
        
        # Check maximum area relative to image
        img_height, img_width = image_shape[:2]
        img_area = img_height * img_width
        if area > img_area * POST_PROCESS_CONFIG["max_bbox_ratio"]:
            return False
        
        # Check aspect ratio
        if height == 0:
            return False
        aspect_ratio = width / height
        if (aspect_ratio < POST_PROCESS_CONFIG["min_aspect_ratio"] or
            aspect_ratio > POST_PROCESS_CONFIG["max_aspect_ratio"]):
            return False
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata and configuration"""
        return {
            "model_path": str(self.model_path),
            "device": self.device,
            "classes": DETECTION_CLASSES,
            "confidence_threshold": self.conf_threshold,
            "nms_threshold": self.nms_threshold,
            "image_size": self.imgsz,
            "post_processing": POST_PROCESS_CONFIG
        }


# Convenience function for quick inference
def detect_objects(
    image: Union[str, Path, np.ndarray, Image.Image],
    model_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Quick inference function - creates detector and runs detection
    
    Args:
        image: Image to process
        model_path: Path to model weights (optional)
        **kwargs: Additional arguments for ObjectDetector
    
    Returns:
        List of detections
    """
    detector = ObjectDetector(model_path=model_path, **kwargs)
    return detector.detect(image)
