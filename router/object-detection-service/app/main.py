"""
FastAPI service for object detection
Provides REST API for detecting signatures, stamps, and QR codes
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import io
import logging
from pathlib import Path

from PIL import Image
import numpy as np

from .detector import ObjectDetector
from .config import SERVICE_NAME, SERVICE_PORT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Object Detection Service",
    description="Detects signatures, stamps, and QR codes in document images",
    version="1.0.0"
)

# Global detector instance
detector: Optional[ObjectDetector] = None


# Pydantic models for API
class Detection(BaseModel):
    """Single detection result"""
    page: int = Field(..., description="Page number (0-indexed)")
    label: str = Field(..., description="Detection class: signature, stamp, or qr_code")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class DetectionResponse(BaseModel):
    """API response with detection results"""
    success: bool
    detections: List[Detection]
    total_count: int
    message: Optional[str] = None


class ModelInfo(BaseModel):
    """Model configuration and metadata"""
    model_path: str
    device: str
    classes: dict
    confidence_threshold: float
    nms_threshold: float
    image_size: int


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global detector
    try:
        logger.info("Initializing object detector...")
        detector = ObjectDetector()
        logger.info("Object detector ready")
    except Exception as e:
        logger.error(f"Failed to initialize detector: {e}")
        # Continue startup - detector can be lazy loaded


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": SERVICE_NAME,
        "status": "running",
        "model_loaded": detector is not None
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "Model not loaded"}
        )
    
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "model_info": detector.get_model_info()
    }


@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """Get model configuration and metadata"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    info = detector.get_model_info()
    return ModelInfo(**info)


@app.post("/detect", response_model=DetectionResponse)
async def detect_objects_endpoint(
    file: UploadFile = File(...),
    page_number: int = Query(0, ge=0, description="Page number for multi-page documents"),
    confidence_threshold: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Override confidence threshold"
    )
):
    """
    Detect objects in uploaded image
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        page_number: Page number (for tracking in multi-page docs)
        confidence_threshold: Optional override for confidence threshold
    
    Returns:
        Detection results
    """
    global detector
    
    # Lazy load detector if not initialized
    if detector is None:
        try:
            detector = ObjectDetector()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize detector: {str(e)}"
            )
    
    # Override confidence if provided
    if confidence_threshold is not None:
        detector.conf_threshold = confidence_threshold
    
    try:
        # Read uploaded file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run detection
        detections = detector.detect(image, page_number=page_number)
        
        return DetectionResponse(
            success=True,
            detections=[Detection(**d) for d in detections],
            total_count=len(detections),
            message=f"Detected {len(detections)} objects"
        )
    
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/batch", response_model=DetectionResponse)
async def detect_batch_endpoint(
    files: List[UploadFile] = File(...),
    confidence_threshold: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Override confidence threshold"
    )
):
    """
    Detect objects in multiple images (batch processing)
    
    Args:
        files: List of image files
        confidence_threshold: Optional override for confidence threshold
    
    Returns:
        Combined detection results from all images
    """
    global detector
    
    if detector is None:
        try:
            detector = ObjectDetector()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize detector: {str(e)}"
            )
    
    if confidence_threshold is not None:
        detector.conf_threshold = confidence_threshold
    
    try:
        all_detections = []
        
        for page_num, file in enumerate(files):
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            detections = detector.detect(image, page_number=page_num)
            all_detections.extend(detections)
        
        return DetectionResponse(
            success=True,
            detections=[Detection(**d) for d in all_detections],
            total_count=len(all_detections),
            message=f"Processed {len(files)} images, found {len(all_detections)} objects"
        )
    
    except Exception as e:
        logger.error(f"Batch detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
