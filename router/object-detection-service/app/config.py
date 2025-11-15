"""
Configuration for Object Detection Service
Model parameters, thresholds, and class mappings
"""
import os
from pathlib import Path

# Service configuration
SERVICE_NAME = "object-detection-service"
SERVICE_PORT = 8007

# Model paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
WEIGHTS_PATH = MODELS_DIR / "best.pt"

# Detection classes
DETECTION_CLASSES = {
    0: "signature",
    1: "stamp",
    2: "qr_code"
}

# Model inference parameters
MODEL_CONFIG = {
    # Confidence threshold for detections
    # Minimum: 0.25 for balanced recall/precision
    # Higher values reduce false positives but may miss valid objects
    "confidence_threshold": 0.35,
    
    # Non-Maximum Suppression (NMS) threshold
    # Controls overlap between boxes - lower = stricter filtering
    # 0.3-0.5 is typical for document elements
    "nms_threshold": 0.4,
    
    # Maximum detections per image
    "max_detections": 100,
    
    # Image size for inference (must match training)
    # YOLOv8/v11 typically uses 640x640
    "imgsz": 640,
    
    # Device: 'cuda' for GPU, 'cpu' for CPU
    "device": "cuda" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu",
    
    # Half precision (FP16) for faster inference on GPU
    "half": False,
    
    # Batch processing
    "batch_size": 1
}

# Class-specific confidence thresholds (optional fine-tuning)
# Override general threshold for specific classes if needed
CLASS_THRESHOLDS = {
    "signature": 0.35,  # Signatures can vary greatly
    "stamp": 0.40,      # Stamps usually more consistent
    "qr_code": 0.45     # QR codes have clear patterns
}

# Post-processing parameters
POST_PROCESS_CONFIG = {
    # Minimum bounding box area (in pixels) to filter out noise
    "min_bbox_area": 100,
    
    # Maximum bounding box area (relative to image size)
    # 0.8 means box can't be larger than 80% of image
    "max_bbox_ratio": 0.8,
    
    # Aspect ratio constraints (width/height)
    "min_aspect_ratio": 0.1,
    "max_aspect_ratio": 10.0
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
