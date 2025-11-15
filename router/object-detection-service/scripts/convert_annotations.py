"""
Convert annotation formats to YOLO format
Supports various input formats and converts to YOLO txt format
"""
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import shutil

from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnnotationConverter:
    """Convert annotations to YOLO format"""
    
    # Class name to ID mapping
    CLASS_MAP = {
        'signature': 0,
        'stamp': 1,
        'qr_code': 2,
        'qr': 2,  # Alias
        'seal': 1,  # Alias for stamp
        'sign': 0,  # Alias for signature
    }
    
    def __init__(self, output_dir: str):
        """
        Args:
            output_dir: Output directory for YOLO format dataset
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.labels_dir = self.output_dir / "labels"
        
        # Create directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_coco_to_yolo(
        self,
        coco_json_path: str,
        images_dir: str
    ):
        """
        Convert COCO format annotations to YOLO format
        
        Args:
            coco_json_path: Path to COCO JSON file
            images_dir: Directory containing images
        """
        logger.info(f"Converting COCO format from {coco_json_path}")
        
        with open(coco_json_path, 'r') as f:
            coco_data = json.load(f)
        
        # Build image ID to filename mapping
        images = {img['id']: img for img in coco_data['images']}
        
        # Build category ID to class ID mapping
        categories = {cat['id']: self._map_class_name(cat['name'])
                     for cat in coco_data['categories']}
        
        # Group annotations by image
        annotations_by_image = {}
        for ann in coco_data['annotations']:
            img_id = ann['image_id']
            if img_id not in annotations_by_image:
                annotations_by_image[img_id] = []
            annotations_by_image[img_id].append(ann)
        
        # Convert each image
        images_dir = Path(images_dir)
        for img_id, annotations in annotations_by_image.items():
            img_info = images[img_id]
            img_filename = img_info['file_name']
            img_width = img_info['width']
            img_height = img_info['height']
            
            # Copy image
            src_img = images_dir / img_filename
            if src_img.exists():
                dst_img = self.images_dir / img_filename
                shutil.copy2(src_img, dst_img)
            else:
                logger.warning(f"Image not found: {src_img}")
                continue
            
            # Convert annotations
            yolo_lines = []
            for ann in annotations:
                class_id = categories.get(ann['category_id'])
                if class_id is None:
                    continue
                
                # COCO bbox: [x, y, width, height]
                x, y, w, h = ann['bbox']
                
                # Convert to YOLO format (normalized center coordinates)
                x_center = (x + w / 2) / img_width
                y_center = (y + h / 2) / img_height
                w_norm = w / img_width
                h_norm = h / img_height
                
                yolo_lines.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
                )
            
            # Save label file
            label_filename = Path(img_filename).stem + '.txt'
            label_path = self.labels_dir / label_filename
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))
        
        logger.info(f"Converted {len(annotations_by_image)} images to YOLO format")
    
    def convert_pascal_voc_to_yolo(
        self,
        annotations_dir: str,
        images_dir: str
    ):
        """
        Convert Pascal VOC format (XML) to YOLO format
        
        Args:
            annotations_dir: Directory containing XML annotation files
            images_dir: Directory containing images
        """
        logger.info(f"Converting Pascal VOC format from {annotations_dir}")
        
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            raise ImportError("xml.etree required for Pascal VOC conversion")
        
        annotations_dir = Path(annotations_dir)
        images_dir = Path(images_dir)
        
        xml_files = list(annotations_dir.glob("*.xml"))
        
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Get image dimensions
            size = root.find('size')
            img_width = int(size.find('width').text)
            img_height = int(size.find('height').text)
            
            # Get image filename
            img_filename = root.find('filename').text
            
            # Copy image
            src_img = images_dir / img_filename
            if src_img.exists():
                dst_img = self.images_dir / img_filename
                shutil.copy2(src_img, dst_img)
            else:
                logger.warning(f"Image not found: {src_img}")
                continue
            
            # Convert objects
            yolo_lines = []
            for obj in root.findall('object'):
                class_name = obj.find('name').text.lower()
                class_id = self._map_class_name(class_name)
                
                if class_id is None:
                    logger.warning(f"Unknown class: {class_name}")
                    continue
                
                bbox = obj.find('bndbox')
                xmin = float(bbox.find('xmin').text)
                ymin = float(bbox.find('ymin').text)
                xmax = float(bbox.find('xmax').text)
                ymax = float(bbox.find('ymax').text)
                
                # Convert to YOLO format
                x_center = ((xmin + xmax) / 2) / img_width
                y_center = ((ymin + ymax) / 2) / img_height
                w_norm = (xmax - xmin) / img_width
                h_norm = (ymax - ymin) / img_height
                
                yolo_lines.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
                )
            
            # Save label file
            label_filename = Path(img_filename).stem + '.txt'
            label_path = self.labels_dir / label_filename
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))
        
        logger.info(f"Converted {len(xml_files)} annotations to YOLO format")
    
    def convert_labelme_to_yolo(
        self,
        labelme_dir: str
    ):
        """
        Convert LabelMe JSON format to YOLO format
        
        Args:
            labelme_dir: Directory containing LabelMe JSON files and images
        """
        logger.info(f"Converting LabelMe format from {labelme_dir}")
        
        labelme_dir = Path(labelme_dir)
        json_files = list(labelme_dir.glob("*.json"))
        
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            img_filename = data['imagePath']
            img_width = data['imageWidth']
            img_height = data['imageHeight']
            
            # Copy image
            src_img = labelme_dir / img_filename
            if src_img.exists():
                dst_img = self.images_dir / img_filename
                shutil.copy2(src_img, dst_img)
            else:
                logger.warning(f"Image not found: {src_img}")
                continue
            
            # Convert shapes
            yolo_lines = []
            for shape in data['shapes']:
                label = shape['label'].lower()
                class_id = self._map_class_name(label)
                
                if class_id is None:
                    logger.warning(f"Unknown class: {label}")
                    continue
                
                # Get bounding box from points
                points = shape['points']
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                
                xmin, xmax = min(xs), max(xs)
                ymin, ymax = min(ys), max(ys)
                
                # Convert to YOLO format
                x_center = ((xmin + xmax) / 2) / img_width
                y_center = ((ymin + ymax) / 2) / img_height
                w_norm = (xmax - xmin) / img_width
                h_norm = (ymax - ymin) / img_height
                
                yolo_lines.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
                )
            
            # Save label file
            label_filename = Path(img_filename).stem + '.txt'
            label_path = self.labels_dir / label_filename
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_lines))
        
        logger.info(f"Converted {len(json_files)} LabelMe annotations to YOLO format")
    
    def _map_class_name(self, class_name: str) -> int:
        """Map class name to class ID"""
        class_name = class_name.lower().strip()
        return self.CLASS_MAP.get(class_name)
    
    def split_dataset(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1
    ):
        """
        Split dataset into train/val/test sets
        
        Args:
            train_ratio: Ratio for training set
            val_ratio: Ratio for validation set
            test_ratio: Ratio for test set
        """
        import random
        
        # Get all image files
        image_files = list(self.images_dir.glob("*.*"))
        random.shuffle(image_files)
        
        n_total = len(image_files)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        train_files = image_files[:n_train]
        val_files = image_files[n_train:n_train + n_val]
        test_files = image_files[n_train + n_val:]
        
        # Create split directories
        for split_name, files in [('train', train_files), ('val', val_files), ('test', test_files)]:
            if not files:
                continue
            
            split_img_dir = self.output_dir / split_name / 'images'
            split_lbl_dir = self.output_dir / split_name / 'labels'
            split_img_dir.mkdir(parents=True, exist_ok=True)
            split_lbl_dir.mkdir(parents=True, exist_ok=True)
            
            for img_file in files:
                # Move image
                shutil.move(str(img_file), str(split_img_dir / img_file.name))
                
                # Move label
                lbl_file = self.labels_dir / (img_file.stem + '.txt')
                if lbl_file.exists():
                    shutil.move(str(lbl_file), str(split_lbl_dir / lbl_file.name))
        
        # Remove original directories
        shutil.rmtree(self.images_dir)
        shutil.rmtree(self.labels_dir)
        
        logger.info(
            f"Dataset split: {len(train_files)} train, "
            f"{len(val_files)} val, {len(test_files)} test"
        )


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="Convert annotations to YOLO format"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        required=True,
        choices=['coco', 'voc', 'labelme'],
        help="Input annotation format"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input directory or file (COCO JSON, VOC XML dir, or LabelMe dir)"
    )
    parser.add_argument(
        "--images",
        type=str,
        help="Images directory (required for COCO and VOC formats)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dataset_yolo",
        help="Output directory for YOLO format dataset (default: dataset_yolo)"
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split dataset into train/val/test"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Training set ratio (default: 0.8)"
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Validation set ratio (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    converter = AnnotationConverter(args.output)
    
    if args.format == 'coco':
        if not args.images:
            raise ValueError("--images required for COCO format")
        converter.convert_coco_to_yolo(args.input, args.images)
    
    elif args.format == 'voc':
        if not args.images:
            raise ValueError("--images required for VOC format")
        converter.convert_pascal_voc_to_yolo(args.input, args.images)
    
    elif args.format == 'labelme':
        converter.convert_labelme_to_yolo(args.input)
    
    if args.split:
        test_ratio = 1.0 - args.train_ratio - args.val_ratio
        converter.split_dataset(args.train_ratio, args.val_ratio, test_ratio)
    
    logger.info("Conversion complete!")


if __name__ == "__main__":
    main()
