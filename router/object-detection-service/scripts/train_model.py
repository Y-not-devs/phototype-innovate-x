"""
Training script for YOLO object detection model
Detects signatures, stamps, and QR codes in documents
"""
import argparse
import yaml
from pathlib import Path
import logging

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("ultralytics not installed. Run: pip install ultralytics")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_data_yaml(
    train_path: str,
    val_path: str,
    output_path: str = "data.yaml",
    test_path: str = None
):
    """
    Create YOLO data configuration file
    
    Args:
        train_path: Path to training images directory
        val_path: Path to validation images directory
        output_path: Output path for data.yaml
        test_path: Optional path to test images directory
    """
    data_config = {
        'train': str(Path(train_path).absolute()),
        'val': str(Path(val_path).absolute()),
        'nc': 3,  # Number of classes
        'names': ['signature', 'stamp', 'qr_code']
    }
    
    if test_path:
        data_config['test'] = str(Path(test_path).absolute())
    
    output_path = Path(output_path)
    with open(output_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False)
    
    logger.info(f"Data config saved to {output_path}")
    return output_path


def train_model(
    data_yaml: str,
    model: str = "yolov8m.pt",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    name: str = "document_detector",
    device: str = "0",
    patience: int = 50,
    **kwargs
):
    """
    Train YOLO model for document object detection
    
    Args:
        data_yaml: Path to data configuration YAML file
        model: Base model to use (yolov8n/s/m/l/x.pt or path to existing weights)
        epochs: Number of training epochs
        imgsz: Input image size
        batch: Batch size
        name: Experiment name
        device: Device to use (0 for GPU, cpu for CPU)
        patience: Early stopping patience
        **kwargs: Additional arguments for YOLO.train()
    """
    logger.info(f"Initializing YOLO model: {model}")
    yolo = YOLO(model)
    
    logger.info("Starting training...")
    results = yolo.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=name,
        device=device,
        patience=patience,
        save=True,
        plots=True,
        **kwargs
    )
    
    logger.info(f"Training complete. Results saved to: runs/detect/{name}")
    logger.info(f"Best weights: runs/detect/{name}/weights/best.pt")
    
    return results


def main():
    """CLI interface for training"""
    parser = argparse.ArgumentParser(
        description="Train YOLO model for document object detection"
    )
    
    # Data configuration
    parser.add_argument(
        "--train",
        type=str,
        required=True,
        help="Path to training images directory"
    )
    parser.add_argument(
        "--val",
        type=str,
        required=True,
        help="Path to validation images directory"
    )
    parser.add_argument(
        "--test",
        type=str,
        default=None,
        help="Path to test images directory (optional)"
    )
    parser.add_argument(
        "--data-yaml",
        type=str,
        default="data.yaml",
        help="Path to save/load data.yaml config (default: data.yaml)"
    )
    
    # Model configuration
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8m.pt",
        help="Base model: yolov8n/s/m/l/x.pt or path to weights (default: yolov8m.pt)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs (default: 100)"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size (default: 640)"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size (default: 16)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device: 0 for GPU, cpu for CPU (default: 0)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="document_detector",
        help="Experiment name (default: document_detector)"
    )
    
    # Training parameters
    parser.add_argument(
        "--patience",
        type=int,
        default=50,
        help="Early stopping patience (default: 50)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.7,
        help="NMS IoU threshold (default: 0.7)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last checkpoint"
    )
    
    # Augmentation
    parser.add_argument(
        "--augment",
        action="store_true",
        default=True,
        help="Use data augmentation (default: True)"
    )
    
    args = parser.parse_args()
    
    # Create data.yaml if paths are provided
    data_yaml_path = Path(args.data_yaml)
    if not data_yaml_path.exists() or args.train:
        logger.info("Creating data configuration...")
        create_data_yaml(
            train_path=args.train,
            val_path=args.val,
            test_path=args.test,
            output_path=args.data_yaml
        )
    
    # Train model
    train_model(
        data_yaml=args.data_yaml,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        name=args.name,
        device=args.device,
        patience=args.patience,
        conf=args.conf,
        iou=args.iou,
        resume=args.resume,
        augment=args.augment
    )


if __name__ == "__main__":
    main()
