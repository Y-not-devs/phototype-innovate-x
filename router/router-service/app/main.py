import os
import asyncio
import logging
import aiohttp
from aiohttp import ClientTimeout
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import cv_pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Router Service", version="1.0.0")

# Service URLs
PREPROCESSOR_SERVICE_URL = "http://127.0.0.1:8001"
LANG_DETECT_SERVICE_URL = "http://127.0.0.1:8002" 
OCR_EN_SERVICE_URL = "http://127.0.0.1:8003"
OCR_RU_SERVICE_URL = "http://127.0.0.1:8004"
OBJECT_DETECTION_SERVICE_URL = "http://127.0.0.1:8006"

class DocumentAnalysisResponse(BaseModel):
    filename: str
    language_detection: Optional[Dict[str, Any]] = None
    preprocessing_result: Optional[Dict[str, Any]] = None
    ocr_result: Optional[Dict[str, Any]] = None
    success: bool
    message: str

@app.get("/healthz")
async def health_check():
    """Health check endpoint with dependent services status"""
    services_status = {}
    
    # Check preprocessor service
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PREPROCESSOR_SERVICE_URL}/healthz", timeout=ClientTimeout(total=2)) as resp:
                services_status["preprocessor"] = "ok" if resp.status == 200 else "error"
    except Exception:
        services_status["preprocessor"] = "unavailable"
    
    # Check lang-detect service
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{LANG_DETECT_SERVICE_URL}/healthz", timeout=ClientTimeout(total=2)) as resp:
                services_status["lang_detect"] = "ok" if resp.status == 200 else "error"
    except Exception:
        services_status["lang_detect"] = "unavailable"
    
    return {
        "status": "ok",
        "service": "router",
        "dependencies": services_status
    }

@app.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Complete document analysis pipeline:
    1. Try language detection directly from PDF
    2. If no text layer, use preprocessor -> OCR -> language detection
    3. Return comprehensive analysis results
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_content = await file.read()
    
    # Step 1: Try direct language detection from PDF
    language_result = await detect_language_from_pdf(file_content, file.filename)
    
    if language_result and language_result.get("success"):
        # PDF has text layer, language detected successfully
        return DocumentAnalysisResponse(
            filename=file.filename,
            language_detection=language_result,
            success=True,
            message="Language detected from PDF text layer"
        )
    
    # Step 2: PDF has no text layer or language detection failed
    # Use preprocessor -> OCR -> language detection pipeline
    try:
        # Preprocess the PDF
        preprocessing_result = await preprocess_pdf(file_content, file.filename)
        
        if not preprocessing_result or not preprocessing_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail="Preprocessing failed"
            )
        
        # Extract text using OCR (we'll use English OCR by default)
        # In a real implementation, we could use language hints or try multiple OCR engines
        ocr_result = await extract_text_with_ocr(preprocessing_result["data"], "en")
        
        if not ocr_result or not ocr_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail="OCR text extraction failed"
            )
        
        # Detect language from extracted text
        extracted_text = ocr_result["data"].get("text", "")
        if extracted_text.strip():
            language_result = await detect_language_from_text(extracted_text)
        
        return DocumentAnalysisResponse(
            filename=file.filename,
            language_detection=language_result,
            preprocessing_result=preprocessing_result,
            ocr_result=ocr_result,
            success=True,
            message="Language detected from OCR text extraction"
        )
        
    except Exception as e:
        return DocumentAnalysisResponse(
            filename=file.filename,
            success=False,
            message=f"Document analysis failed: {str(e)}"
        )

async def detect_language_from_pdf(file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Try to detect language directly from PDF text layer"""
    logger.info(f"Attempting to detect language from PDF: {filename}")
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type='application/pdf')
            
            async with session.post(
                f"{LANG_DETECT_SERVICE_URL}/detect-language",
                data=data,
                timeout=ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                elif response.status == 422:
                    # No text layer in PDF
                    return {"success": False, "reason": "no_text_layer"}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def detect_language_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Detect language from extracted text"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"text": text}
            
            async with session.post(
                f"{LANG_DETECT_SERVICE_URL}/detect-text",
                json=payload,
                timeout=ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def preprocess_pdf(file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Preprocess PDF using the preprocessor service"""
    logger.info(f"Preprocessing PDF: {filename}")
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type='application/pdf')
            
            async with session.post(
                f"{PREPROCESSOR_SERVICE_URL}/preprocess/",
                data=data,
                timeout=ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def extract_text_with_ocr(preprocessing_data: Dict[str, Any], language: str = "en") -> Optional[Dict[str, Any]]:
    """Extract text from preprocessed images using OCR"""
    # This is a placeholder implementation
    # In a real scenario, you would:
    # 1. Take the segmented images from preprocessing_data
    # 2. Send them to the appropriate OCR service based on detected/specified language
    # 3. Combine the OCR results into coherent text
    
    # For now, we'll return a mock successful response
    # because the OCR services are not enabled in run.py
    
    try:
        saved_files = preprocessing_data.get("saved_files", [])
        
        # Mock OCR extraction
        # In reality, you would process each image file through OCR
        mock_text = "This is extracted text from OCR processing. " * len(saved_files)
        
        return {
            "success": True,
            "data": {
                "text": mock_text,
                "processed_files": saved_files,
                "ocr_language": language,
                "method": "mock_ocr"  # Remove this in real implementation
            }
        }
        
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}


@app.post("/analyze-document-cv")
async def analyze_document_cv(
    file: UploadFile = File(...),
    return_annotated: bool = False
):
    """
    Analyze document (image or PDF) for stamps, signatures, and QR codes using CV pipeline.
    
    Args:
        file: Uploaded image or PDF file
        return_annotated: If True, saves and returns path to annotated image
    
    Returns:
        JSON with detection results and optionally annotated image path
    """
    logger.info(f"CV analysis request received for file: {file.filename}")
    
    # Validate file type
    if file.filename:
        filename_lower = file.filename.lower()
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
    else:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    temp_input_file = None
    temp_output_dir = None
    
    try:
        # Import cv_pipeline
        try:
            from cv_pipeline import DocumentAnalysisPipeline
        except ImportError:
            logger.error("Failed to import cv_pipeline. Make sure it exists in router directory.")
            raise HTTPException(status_code=500, detail="CV pipeline not available")
        
        # Save uploaded file to temporary location
        temp_input_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(file.filename).suffix
        )
        
        # Read and save file content
        content = await file.read()
        temp_input_file.write(content)
        temp_input_file.close()
        
        logger.info(f"File saved to temporary location: {temp_input_file.name}")
        
        # Create temporary output directory for annotated images
        temp_output_dir = tempfile.mkdtemp(prefix="cv_analysis_")
        
        # Initialize pipeline
        # Use GPU if available, otherwise CPU
        pipeline = DocumentAnalysisPipeline(
            model_path=None,  # Will use mock detector if model not available
            use_gpu=False  # Change to True if GPU available and configured
        )
        
        logger.info("Starting CV analysis...")
        
        # Analyze document
        # output_dir is passed only if annotated images are requested
        results = pipeline.analyze_file(
            file_path=temp_input_file.name,
            output_dir=temp_output_dir if return_annotated else None
        )
        
        logger.info(f"CV analysis completed. Found {results['total_detections']} objects.")
        
        # Prepare response
        response_data = {
            "success": True,
            "filename": file.filename,
            "file_type": "pdf" if file.filename.lower().endswith('.pdf') else "image",
            "total_pages": results.get("total_pages", 1),
            "total_detections": results["total_detections"],
            "summary": results["summary"],
            "pages": results["pages"]
        }
        
        # If annotated images requested, include their paths
        if return_annotated and results.get("annotated_images"):
            response_data["annotated_images"] = results["annotated_images"]
            response_data["output_directory"] = temp_output_dir
            logger.info(f"Annotated images saved to: {temp_output_dir}")
        
        return response_data
        
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import required modules: {str(e)}")
    
    except Exception as e:
        logger.error(f"CV analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Clean up temporary input file
        if temp_input_file and os.path.exists(temp_input_file.name):
            try:
                os.unlink(temp_input_file.name)
                logger.info("Temporary input file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")
        
        # Note: temp_output_dir is NOT deleted here if annotated images were requested
        # Frontend should download them, then call a cleanup endpoint
        # Or implement auto-cleanup after certain time


@app.get("/download-annotated/{filename}")
async def download_annotated_image(filename: str, output_dir: str):
    """
    Download annotated image from temporary directory.
    
    Args:
        filename: Name of the annotated image file
        output_dir: Path to the output directory containing the file
    
    Returns:
        FileResponse with the annotated image
    """
    file_path = os.path.join(output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="image/png"
    )


@app.post("/cleanup-temp/{output_dir:path}")
async def cleanup_temp_directory(output_dir: str):
    """
    Clean up temporary output directory after downloading annotated images.
    
    Args:
        output_dir: Path to the temporary directory to remove
    
    Returns:
        Success status
    """
    try:
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
            logger.info(f"Cleaned up temporary directory: {output_dir}")
            return {"success": True, "message": "Directory cleaned up successfully"}
        else:
            raise HTTPException(status_code=404, detail="Directory not found")
    
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
