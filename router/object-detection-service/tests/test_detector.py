"""
Unit tests for object detection service
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.detector import ObjectDetector, detect_objects
from app.config import DETECTION_CLASSES, MODEL_CONFIG

# Skip tests if model not available
MODEL_EXISTS = Path(__file__).parent.parent / "models" / "best.pt"
pytestmark = pytest.mark.skipif(
    not MODEL_EXISTS.exists(),
    reason="Model weights not found. Train model first."
)


class TestObjectDetector:
    """Test ObjectDetector class"""
    
    def test_detector_initialization(self):
        """Test detector can be initialized"""
        if MODEL_EXISTS.exists():
            detector = ObjectDetector()
            assert detector is not None
            assert detector.model is not None
    
    def test_get_model_info(self):
        """Test model info retrieval"""
        if MODEL_EXISTS.exists():
            detector = ObjectDetector()
            info = detector.get_model_info()
            
            assert "model_path" in info
            assert "device" in info
            assert "classes" in info
            assert info["classes"] == DETECTION_CLASSES
    
    def test_detection_format(self):
        """Test detection output format"""
        # Mock test - would need real image
        expected_keys = {"page", "label", "bbox", "confidence"}
        # This would be filled with actual test when model is available
        pass


class TestConfig:
    """Test configuration"""
    
    def test_detection_classes(self):
        """Test detection classes are properly defined"""
        assert 0 in DETECTION_CLASSES
        assert 1 in DETECTION_CLASSES
        assert 2 in DETECTION_CLASSES
        assert DETECTION_CLASSES[0] == "signature"
        assert DETECTION_CLASSES[1] == "stamp"
        assert DETECTION_CLASSES[2] == "qr_code"
    
    def test_model_config(self):
        """Test model configuration has required keys"""
        required_keys = {
            "confidence_threshold",
            "nms_threshold",
            "max_detections",
            "imgsz",
            "device"
        }
        assert all(key in MODEL_CONFIG for key in required_keys)
        
        # Check value ranges
        assert 0 < MODEL_CONFIG["confidence_threshold"] < 1
        assert 0 < MODEL_CONFIG["nms_threshold"] < 1
        assert MODEL_CONFIG["max_detections"] > 0
        assert MODEL_CONFIG["imgsz"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
