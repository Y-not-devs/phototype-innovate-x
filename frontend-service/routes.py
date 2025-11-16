"""
API routes for the Phototype application
"""
from flask import render_template, request, jsonify
import cv2
import numpy as np
import time

from detection import generate_mock_detections


def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def index():
        """Main page"""
        return render_template('index.html')

    @app.route('/api/analyze', methods=['POST'])
    def analyze_image():
        """
        API endpoint for image analysis
        Accepts an image and returns detected objects
        """
        try:
            # Get file from request
            if 'image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
            
            file = request.files['image']
            
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
            # Read image
            image_bytes = file.read()
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return jsonify({'error': 'Invalid image'}), 400
            
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Processing simulation (in production, this will be a Computer Vision model)
            time.sleep(1)  # Simulate processing time
            
            # Generate mock results (replace with real CV model)
            detections = generate_mock_detections()
            
            # Format response
            response = {
                'success': True,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
                'image_dimensions': {
                    'width': int(width),
                    'height': int(height)
                },
                'detections': detections,
                'summary': {
                    'total_detections': len(detections),
                    'signatures': len([d for d in detections if d['type'] == 'signature']),
                    'stamps': len([d for d in detections if d['type'] == 'stamp']),
                    'qr_codes': len([d for d in detections if d['type'] == 'qr-code'])
                }
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Server health check"""
        return jsonify({
            'status': 'healthy',
            'message': 'Phototype API is running'
        }), 200
