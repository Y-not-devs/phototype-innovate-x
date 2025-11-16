"""
Unified Computer Vision Pipeline for Document Analysis
Detects signatures, stamps, and QR codes in images and PDFs

This module integrates:
1. Preprocessor - PDF to image conversion and enhancement
2. Object Detection - YOLO-based detection of signatures, stamps, QR codes
3. Postprocessor - Results aggregation and formatting
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional, Tuple
import tempfile
import json

import numpy as np
import cv2
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentAnalysisPipeline:
    """
    Complete CV pipeline for document analysis
    Supports both images and PDF files
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_gpu: bool = False,
        confidence_threshold: float = 0.35
    ):
        """
        Initialize the document analysis pipeline
        
        Args:
            model_path: Path to YOLO model weights
            use_gpu: Use GPU for inference if available
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self.detector = None
        
        logger.info("Initializing Document Analysis Pipeline")
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize YOLO detector"""
        try:
            from ultralytics import YOLO  # type: ignore
            
            if self.model_path and Path(self.model_path).exists():
                logger.info(f"Loading YOLO model from {self.model_path}")
                self.detector = YOLO(self.model_path)
            else:
                logger.warning("Model weights not found. Using mock detector.")
                self.detector = None
        except ImportError:
            logger.warning("Ultralytics not installed. Using mock detector.")
            self.detector = None
    
    def analyze_file(
        self,
        file_path: Union[str, Path],
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze image or PDF file for signatures, stamps, and QR codes
        
        Args:
            file_path: Path to image or PDF file
            output_dir: Optional directory to save annotated images
        
        Returns:
            Dictionary with detection results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._analyze_pdf(file_path, output_dir)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self._analyze_image(file_path, output_dir)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _analyze_pdf(
        self,
        pdf_path: Path,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze PDF file page by page
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save results
        
        Returns:
            Combined detection results from all pages
        """
        logger.info(f"Analyzing PDF: {pdf_path}")
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=300)
            logger.info(f"Converted PDF to {len(images)} pages")
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            raise
        
        all_detections = []
        page_results = []
        
        for page_num, image in enumerate(images, start=1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            # Preprocess image
            processed_img = self._preprocess_image(image)
            
            # Detect objects
            detections = self._detect_objects(processed_img, page_num)
            
            # Store results
            page_results.append({
                "page": page_num,
                "detections": detections,
                "detection_count": len(detections)
            })
            
            all_detections.extend(detections)
            
            # Save annotated image if output_dir specified
            if output_dir:
                self._save_annotated_image(
                    processed_img,
                    detections,
                    Path(output_dir) / f"page_{page_num:03d}_annotated.jpg"
                )
        
        # Compile results
        results = {
            "file_name": pdf_path.name,
            "file_type": "pdf",
            "total_pages": len(images),
            "total_detections": len(all_detections),
            "detection_summary": self._summarize_detections(all_detections),
            "page_results": page_results,
            "all_detections": all_detections
        }
        
        return results
    
    def _analyze_image(
        self,
        image_path: Path,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze single image file
        
        Args:
            image_path: Path to image file
            output_dir: Optional directory to save results
        
        Returns:
            Detection results
        """
        logger.info(f"Analyzing image: {image_path}")
        
        # Load image
        image = Image.open(image_path)
        
        # Preprocess
        processed_img = self._preprocess_image(image)
        
        # Detect objects
        detections = self._detect_objects(processed_img, page_num=1)
        
        # Save annotated image if output_dir specified
        if output_dir:
            self._save_annotated_image(
                processed_img,
                detections,
                Path(output_dir) / f"{image_path.stem}_annotated.jpg"
            )
        
        # Compile results
        results = {
            "file_name": image_path.name,
            "file_type": "image",
            "total_pages": 1,
            "total_detections": len(detections),
            "detection_summary": self._summarize_detections(detections),
            "all_detections": detections
        }
        
        return results
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for better detection
        
        Args:
            image: PIL Image
        
        Returns:
            Preprocessed numpy array (BGR format for OpenCV)
        """
        # Convert to numpy array
        img_array = np.array(image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Deskew if needed
        img_bgr = self._deskew_image(img_bgr)
        
        # Denoise
        img_bgr = cv2.fastNlMeansDenoisingColored(img_bgr, None, 10, 10, 7, 21)
        
        return img_bgr
    
    def _deskew_image(self, img: np.ndarray) -> np.ndarray:
        """
        Detect and correct image skew
        
        Args:
            img: Input image (BGR)
        
        Returns:
            Deskewed image
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180.0,
            threshold=80,
            minLineLength=min(gray.shape) // 4,
            maxLineGap=20
        )
        
        if lines is None:
            return img
        
        angles = []
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            dx, dy = x2 - x1, y2 - y1
            angle = 90.0 if dx == 0 else np.degrees(np.arctan2(dy, dx))
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return img
        
        angle = float(np.median(angles))
        
        if abs(angle) > 0.2:
            (h, w) = img.shape[:2]
            center = (w / 2.0, h / 2.0)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(
                img, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
        
        return img
    
    def _detect_objects(
        self,
        image: np.ndarray,
        page_num: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Detect signatures, stamps, and QR codes in image
        
        Args:
            image: Image as numpy array (BGR)
            page_num: Page number for PDF files
        
        Returns:
            List of detections
        """
        if self.detector is None:
            # Use mock detections for demonstration
            return self._generate_mock_detections(image, page_num)
        
        try:
            # Run YOLO inference
            results = self.detector.predict(
                image,
                conf=self.confidence_threshold,
                device='cuda' if self.use_gpu else 'cpu',
                verbose=False
            )
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                # Check if boxes exist
                if boxes is None or len(boxes) == 0:
                    continue
                
                for box in boxes:
                    # Extract box data
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls = int(box.cls[0].cpu().numpy())
                    
                    # Map class ID to label
                    label_map = {0: "signature", 1: "stamp", 2: "qr_code"}
                    label = label_map.get(cls, "unknown")
                    
                    detections.append({
                        "page": page_num,
                        "label": label,
                        "confidence": round(conf, 3),
                        "bbox": {
                            "x1": int(xyxy[0]),
                            "y1": int(xyxy[1]),
                            "x2": int(xyxy[2]),
                            "y2": int(xyxy[3])
                        }
                    })
            
            logger.info(f"Found {len(detections)} objects on page {page_num}")
            return detections
        
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def _generate_mock_detections(
        self,
        image: np.ndarray,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """Generate mock detections for demonstration"""
        h, w = image.shape[:2]
        
        detections = [
            {
                "page": page_num,
                "label": "signature",
                "confidence": 0.92,
                "bbox": {
                    "x1": int(w * 0.1),
                    "y1": int(h * 0.7),
                    "x2": int(w * 0.3),
                    "y2": int(h * 0.85)
                }
            },
            {
                "page": page_num,
                "label": "stamp",
                "confidence": 0.88,
                "bbox": {
                    "x1": int(w * 0.7),
                    "y1": int(h * 0.15),
                    "x2": int(w * 0.9),
                    "y2": int(h * 0.35)
                }
            }
        ]
        
        logger.info(f"Generated {len(detections)} mock detections")
        return detections
    
    def _summarize_detections(
        self,
        detections: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Summarize detections by type
        
        Args:
            detections: List of detection dictionaries
        
        Returns:
            Summary counts by type
        """
        summary = {"signature": 0, "stamp": 0, "qr_code": 0}
        
        for detection in detections:
            label = detection.get("label", "unknown")
            if label in summary:
                summary[label] += 1
        
        return summary
    
    def _save_annotated_image(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        output_path: Path
    ):
        """
        Save image with detection boxes drawn
        
        Args:
            image: Image array (BGR)
            detections: List of detections
            output_path: Path to save annotated image
        """
        # Create copy
        annotated = image.copy()
        
        # Color mapping
        colors = {
            "signature": (0, 255, 0),      # Green
            "stamp": (255, 0, 0),          # Blue
            "qr_code": (0, 0, 255)         # Red
        }
        
        # Draw boxes
        for det in detections:
            bbox = det["bbox"]
            label = det["label"]
            conf = det["confidence"]
            color = colors.get(label, (255, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(
                annotated,
                (bbox["x1"], bbox["y1"]),
                (bbox["x2"], bbox["y2"]),
                color,
                2
            )
            
            # Draw label
            text = f"{label} {conf:.2f}"
            cv2.putText(
                annotated,
                text,
                (bbox["x1"], bbox["y1"] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), annotated)
        logger.info(f"Saved annotated image to {output_path}")


def analyze_document(
    file_path: str,
    output_dir: Optional[str] = None,
    model_path: Optional[str] = None,
    use_gpu: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to analyze a document
    
    Args:
        file_path: Path to image or PDF file
        output_dir: Optional directory to save annotated images
        model_path: Optional path to YOLO model weights
        use_gpu: Use GPU for inference
    
    Returns:
        Detection results dictionary
    """
    pipeline = DocumentAnalysisPipeline(
        model_path=model_path,
        use_gpu=use_gpu
    )
    
    results = pipeline.analyze_file(file_path, output_dir)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze documents for signatures, stamps, and QR codes"
    )
    parser.add_argument("file", help="Path to image or PDF file")
    parser.add_argument(
        "-o", "--output",
        help="Output directory for annotated images",
        default="output"
    )
    parser.add_argument(
        "-m", "--model",
        help="Path to YOLO model weights",
        default=None
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for inference"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Analyze document
    results = analyze_document(
        args.file,
        args.output,
        args.model,
        args.gpu
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Document: {results['file_name']}")
    print(f"Type: {results['file_type'].upper()}")
    print(f"Total Detections: {results['total_detections']}")
    print(f"\nDetection Summary:")
    for label, count in results['detection_summary'].items():
        print(f"  {label.capitalize()}: {count}")
    print(f"{'='*60}\n")
    
    # Save JSON if requested
    if args.save_json:
        json_path = Path(args.output) / f"{Path(args.file).stem}_results.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {json_path}")
