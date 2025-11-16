"""
Computer Vision detection functions for identifying signatures, stamps, and QR codes
"""
import cv2
import random


def generate_mock_detections():
    """
    Generates mock data for demonstration
    In production, replace with actual CV model call
    """
    types = ['signature', 'stamp', 'qr-code']
    labels = {
        'signature': 'Signature',
        'stamp': 'Stamp',
        'qr-code': 'QR Code'
    }
    
    detections = []
    num_detections = random.randint(3, 8)
    
    for i in range(num_detections):
        detection_type = random.choice(types)
        x = round(random.uniform(0.1, 0.7), 3)
        y = round(random.uniform(0.1, 0.7), 3)
        w = round(random.uniform(0.1, 0.25), 3)
        h = round(random.uniform(0.1, 0.25), 3)
        
        detections.append({
            'type': detection_type,
            'label': labels[detection_type],
            'confidence': round(random.uniform(0.85, 0.99), 3),
            'bounding_box': {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }
        })
    
    return detections


def detect_signatures(image):
    """
    Real function for signature detection
    CV model logic should be implemented here
    """
    # TODO: Implement real signature detection
    pass


def detect_stamps(image):
    """
    Real function for stamp detection
    CV model logic should be implemented here
    """
    # TODO: Implement real stamp detection
    pass


def detect_qr_codes(image):
    """
    Real function for QR code detection
    """
    # Example using OpenCV for QR codes
    qr_detector = cv2.QRCodeDetector()
    data, bbox, _ = qr_detector.detectAndDecode(image)
    
    detections = []
    if bbox is not None:
        # Normalize coordinates
        height, width = image.shape[:2]
        for box in bbox:
            x_min = float(min(box[:, 0])) / width
            y_min = float(min(box[:, 1])) / height
            x_max = float(max(box[:, 0])) / width
            y_max = float(max(box[:, 1])) / height
            
            detections.append({
                'type': 'qr-code',
                'label': 'QR Code',
                'confidence': 0.99,
                'data': data,
                'bounding_box': {
                    'x': round(x_min, 3),
                    'y': round(y_min, 3),
                    'width': round(x_max - x_min, 3),
                    'height': round(y_max - y_min, 3)
                }
            })
    
    return detections
