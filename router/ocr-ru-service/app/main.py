"""
OCR Russian Service
Extracts text from images using Tesseract OCR for Russian language
"""
import logging
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OCR Russian Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OCRResponse(BaseModel):
    """OCR response model"""
    success: bool
    text: str
    confidence: float
    language: str = "rus"
    message: str = ""


@app.get("/healthz")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "ocr-ru"}


@app.post("/ocr", response_model=OCRResponse)
async def extract_text(file: UploadFile = File(...)):
    """
    Extract text from image using Russian OCR
    
    Args:
        file: Image file (PNG, JPG, etc.)
    
    Returns:
        Extracted text and confidence score
    """
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # TODO: Implement actual Tesseract OCR with Russian language
        # For now, return mock response
        logger.warning("Using mock OCR response - Tesseract not implemented yet")
        
        return OCRResponse(
            success=True,
            text="[Mock OCR Text RU] Это заполнитель текста, извлеченного из изображения.",
            confidence=0.95,
            language="rus",
            message="Mock OCR - Tesseract integration pending"
        )
    
    except Exception as e:
        logger.error(f"OCR error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr-batch", response_model=Dict[str, Any])
async def extract_text_batch(files: List[UploadFile] = File(...)):
    """
    Extract text from multiple images
    
    Args:
        files: List of image files
    
    Returns:
        Combined OCR results
    """
    try:
        results = []
        
        for idx, file in enumerate(files):
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # TODO: Implement actual Tesseract OCR
            logger.warning(f"Using mock OCR for file {idx}: {file.filename}")
            
            results.append({
                "filename": file.filename,
                "text": f"[Mock OCR Text RU {idx}] Заполнитель текста.",
                "confidence": 0.95,
                "page": idx
            })
        
        return {
            "success": True,
            "results": results,
            "total_files": len(files),
            "language": "rus"
        }
    
    except Exception as e:
        logger.error(f"Batch OCR error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
