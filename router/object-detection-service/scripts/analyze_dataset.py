"""
Dataset analysis and preparation utilities for YOLO training
Analyzes document dataset for signatures, stamps, and QR codes
"""
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import logging

from PIL import Image
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetAnalyzer:
    """
    Analyze dataset characteristics for object detection training
    """
    
    def __init__(self, dataset_path: str):
        """
        Args:
            dataset_path: Path to dataset directory
        """
        self.dataset_path = Path(dataset_path)
        self.images_path = self.dataset_path / "images"
        self.labels_path = self.dataset_path / "labels"
        
        if not self.images_path.exists():
            logger.warning(f"Images directory not found: {self.images_path}")
        if not self.labels_path.exists():
            logger.warning(f"Labels directory not found: {self.labels_path}")
    
    def analyze(self) -> Dict:
        """
        Perform comprehensive dataset analysis
        
        Returns:
            Dictionary with analysis results
        """
        logger.info("Starting dataset analysis...")
        
        analysis = {
            "dataset_path": str(self.dataset_path),
            "image_stats": self._analyze_images(),
            "annotation_stats": self._analyze_annotations(),
            "class_distribution": self._analyze_class_distribution(),
            "object_sizes": self._analyze_object_sizes(),
            "recommendations": []
        }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_images(self) -> Dict:
        """Analyze image characteristics"""
        if not self.images_path.exists():
            return {"error": "Images directory not found"}
        
        image_files = list(self.images_path.glob("*.jpg")) + \
                      list(self.images_path.glob("*.png")) + \
                      list(self.images_path.glob("*.jpeg"))
        
        if not image_files:
            return {"error": "No image files found"}
        
        resolutions = []
        formats = Counter()
        file_sizes = []
        
        for img_path in image_files:
            try:
                img = Image.open(img_path)
                resolutions.append(img.size)
                formats[img.format] += 1
                file_sizes.append(img_path.stat().st_size)
            except Exception as e:
                logger.warning(f"Failed to process {img_path}: {e}")
        
        widths, heights = zip(*resolutions) if resolutions else ([], [])
        
        return {
            "total_images": len(image_files),
            "formats": dict(formats),
            "resolution_stats": {
                "min_width": min(widths) if widths else 0,
                "max_width": max(widths) if widths else 0,
                "avg_width": sum(widths) / len(widths) if widths else 0,
                "min_height": min(heights) if heights else 0,
                "max_height": max(heights) if heights else 0,
                "avg_height": sum(heights) / len(heights) if heights else 0,
            },
            "file_size_stats": {
                "min_mb": min(file_sizes) / (1024*1024) if file_sizes else 0,
                "max_mb": max(file_sizes) / (1024*1024) if file_sizes else 0,
                "avg_mb": sum(file_sizes) / len(file_sizes) / (1024*1024) if file_sizes else 0,
            }
        }
    
    def _analyze_annotations(self) -> Dict:
        """Analyze annotation files"""
        if not self.labels_path.exists():
            return {"error": "Labels directory not found"}
        
        label_files = list(self.labels_path.glob("*.txt"))
        
        if not label_files:
            return {"error": "No label files found"}
        
        total_objects = 0
        images_with_objects = 0
        empty_images = 0
        
        for label_file in label_files:
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        total_objects += len(lines)
                        images_with_objects += 1
                    else:
                        empty_images += 1
            except Exception as e:
                logger.warning(f"Failed to read {label_file}: {e}")
        
        return {
            "total_label_files": len(label_files),
            "total_objects": total_objects,
            "images_with_objects": images_with_objects,
            "empty_images": empty_images,
            "avg_objects_per_image": total_objects / len(label_files) if label_files else 0
        }
    
    def _analyze_class_distribution(self) -> Dict:
        """Analyze distribution of classes"""
        if not self.labels_path.exists():
            return {"error": "Labels directory not found"}
        
        class_counts = Counter()
        
        label_files = list(self.labels_path.glob("*.txt"))
        
        for label_file in label_files:
            try:
                with open(label_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            class_id = int(parts[0])
                            class_counts[class_id] += 1
            except Exception as e:
                logger.warning(f"Failed to parse {label_file}: {e}")
        
        # Map class IDs to names
        class_names = {0: "signature", 1: "stamp", 2: "qr_code"}
        distribution = {
            class_names.get(cls_id, f"class_{cls_id}"): count
            for cls_id, count in class_counts.items()
        }
        
        total = sum(distribution.values())
        percentages = {
            cls: f"{(count/total*100):.1f}%"
            for cls, count in distribution.items()
        } if total > 0 else {}
        
        return {
            "distribution": distribution,
            "percentages": percentages,
            "total_objects": total,
            "balance_ratio": max(distribution.values()) / min(distribution.values())
                            if distribution and min(distribution.values()) > 0 else None
        }
    
    def _analyze_object_sizes(self) -> Dict:
        """Analyze bounding box sizes and aspect ratios"""
        if not self.labels_path.exists():
            return {"error": "Labels directory not found"}
        
        widths = []
        heights = []
        areas = []
        aspect_ratios = []
        
        label_files = list(self.labels_path.glob("*.txt"))
        
        for label_file in label_files:
            # Get corresponding image to calculate absolute sizes
            img_file = self.images_path / label_file.with_suffix('.jpg').name
            if not img_file.exists():
                img_file = self.images_path / label_file.with_suffix('.png').name
            
            if not img_file.exists():
                continue
            
            try:
                img = Image.open(img_file)
                img_width, img_height = img.size
                
                with open(label_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            # YOLO format: class x_center y_center width height (normalized)
                            w_norm = float(parts[3])
                            h_norm = float(parts[4])
                            
                            w_abs = w_norm * img_width
                            h_abs = h_norm * img_height
                            
                            widths.append(w_abs)
                            heights.append(h_abs)
                            areas.append(w_abs * h_abs)
                            
                            if h_abs > 0:
                                aspect_ratios.append(w_abs / h_abs)
            
            except Exception as e:
                logger.warning(f"Failed to analyze sizes in {label_file}: {e}")
        
        if not widths:
            return {"error": "No valid bounding boxes found"}
        
        return {
            "width_stats": {
                "min": min(widths),
                "max": max(widths),
                "avg": sum(widths) / len(widths),
                "median": sorted(widths)[len(widths)//2]
            },
            "height_stats": {
                "min": min(heights),
                "max": max(heights),
                "avg": sum(heights) / len(heights),
                "median": sorted(heights)[len(heights)//2]
            },
            "area_stats": {
                "min": min(areas),
                "max": max(areas),
                "avg": sum(areas) / len(areas)
            },
            "aspect_ratio_stats": {
                "min": min(aspect_ratios),
                "max": max(aspect_ratios),
                "avg": sum(aspect_ratios) / len(aspect_ratios)
            },
            "total_boxes_analyzed": len(widths)
        }
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check image count
        img_stats = analysis.get("image_stats", {})
        total_images = img_stats.get("total_images", 0)
        
        if total_images < 100:
            recommendations.append(
                f"⚠️ Low image count ({total_images}). Recommend at least 300-500 images per class."
            )
        elif total_images < 500:
            recommendations.append(
                f"⚠️ Moderate dataset size ({total_images}). Consider augmentation to reach 1000+ images."
            )
        
        # Check class balance
        class_dist = analysis.get("class_distribution", {})
        balance_ratio = class_dist.get("balance_ratio")
        
        if balance_ratio and balance_ratio > 3:
            recommendations.append(
                f"⚠️ Class imbalance detected (ratio: {balance_ratio:.1f}:1). "
                "Consider oversampling minority classes or using class weights."
            )
        
        # Check resolution
        res_stats = img_stats.get("resolution_stats", {})
        avg_width = res_stats.get("avg_width", 0)
        avg_height = res_stats.get("avg_height", 0)
        
        if avg_width < 640 or avg_height < 640:
            recommendations.append(
                f"⚠️ Low average resolution ({avg_width:.0f}x{avg_height:.0f}). "
                "May affect small object detection. Consider upscaling or using smaller model input size."
            )
        
        # Check object sizes
        obj_sizes = analysis.get("object_sizes", {})
        if "area_stats" in obj_sizes:
            min_area = obj_sizes["area_stats"].get("min", 0)
            if min_area < 100:
                recommendations.append(
                    "⚠️ Very small objects detected (area < 100 pixels). "
                    "Use multi-scale training and lower confidence thresholds."
                )
        
        if not recommendations:
            recommendations.append("✓ Dataset looks good for training!")
        
        return recommendations
    
    def save_report(self, output_path: str):
        """Save analysis report to JSON file"""
        analysis = self.analyze()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis report saved to {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("DATASET ANALYSIS SUMMARY")
        print("="*60)
        
        if "image_stats" in analysis:
            print(f"\nImages: {analysis['image_stats'].get('total_images', 0)}")
        
        if "class_distribution" in analysis:
            print("\nClass Distribution:")
            dist = analysis["class_distribution"].get("distribution", {})
            for cls, count in dist.items():
                pct = analysis["class_distribution"]["percentages"].get(cls, "")
                print(f"  {cls}: {count} ({pct})")
        
        print("\nRecommendations:")
        for rec in analysis.get("recommendations", []):
            print(f"  {rec}")
        
        print("="*60 + "\n")


def main():
    """CLI interface for dataset analysis"""
    parser = argparse.ArgumentParser(
        description="Analyze document dataset for YOLO training"
    )
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Path to dataset directory (should contain images/ and labels/ subdirs)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="dataset_analysis.json",
        help="Output path for analysis report (default: dataset_analysis.json)"
    )
    
    args = parser.parse_args()
    
    analyzer = DatasetAnalyzer(args.dataset_path)
    analyzer.save_report(args.output)


if __name__ == "__main__":
    main()
