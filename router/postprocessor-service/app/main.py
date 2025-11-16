"""
Postprocessor Service
Post-processes OCR and detection results, combining and formatting data
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Postprocessor Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OCRResult(BaseModel):
    """OCR result model"""
    text: str
    confidence: float
    language: str


class DetectionResult(BaseModel):
    """Detection result model"""
    label: str
    bbox: List[float]
    confidence: float
    page: int


class PostprocessRequest(BaseModel):
    """Postprocess request model"""
    ocr_results: Optional[List[OCRResult]] = None
    detection_results: Optional[List[DetectionResult]] = None
    metadata: Optional[Dict[str, Any]] = None


class PostprocessResponse(BaseModel):
    """Postprocess response model"""
    success: bool
    combined_text: str
    detections_summary: Dict[str, int]
    confidence_avg: float
    metadata: Dict[str, Any]


@app.get("/healthz")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "postprocessor"}


@app.post("/postprocess", response_model=PostprocessResponse)
async def postprocess(request: PostprocessRequest):
    """
    Post-process OCR and detection results
    
    Args:
        request: Combined OCR and detection results
    
    Returns:
        Formatted and combined results
    """
    try:
        # Combine OCR texts
        combined_text = ""
        total_confidence = 0.0
        ocr_count = 0
        
        if request.ocr_results:
            texts = [result.text for result in request.ocr_results]
            combined_text = "\n\n".join(texts)
            
            confidences = [result.confidence for result in request.ocr_results]
            total_confidence = sum(confidences)
            ocr_count = len(confidences)
        
        # Summarize detections
        detections_summary = {}
        if request.detection_results:
            for detection in request.detection_results:
                label = detection.label
                detections_summary[label] = detections_summary.get(label, 0) + 1
        
        # Calculate average confidence
        avg_confidence = total_confidence / ocr_count if ocr_count > 0 else 0.0
        
        # Build metadata
        metadata = request.metadata or {}
        metadata.update({
            "total_ocr_results": ocr_count,
            "total_detections": len(request.detection_results or []),
            "processing_complete": True
        })
        
        return PostprocessResponse(
            success=True,
            combined_text=combined_text,
            detections_summary=detections_summary,
            confidence_avg=avg_confidence,
            metadata=metadata
        )
    
    except Exception as e:
        logger.error(f"Postprocessing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/format-json")
async def format_json(request: PostprocessRequest):
    """
    Format results as structured JSON
    
    Args:
        request: Combined results
    
    Returns:
        Structured JSON output
    """
    try:
        output = {
            "ocr": {
                "results": [result.dict() for result in (request.ocr_results or [])],
                "count": len(request.ocr_results or [])
            },
            "detections": {
                "results": [det.dict() for det in (request.detection_results or [])],
                "count": len(request.detection_results or [])
            },
            "metadata": request.metadata or {}
        }
        
        return output
    
    except Exception as e:
        logger.error(f"JSON formatting error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
