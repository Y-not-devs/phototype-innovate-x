/**
 * Canvas Drawing Module
 * Handles canvas operations and detection visualization
 */

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

/**
 * Display image on canvas
 * @param {Image} img - Image to display
 */
export function displayImage(img) {
    const maxWidth = canvas.parentElement.clientWidth - 64;
    const maxHeight = 600;
    
    let width = img.width;
    let height = img.height;
    
    if (width > maxWidth) {
        height = (maxWidth / width) * height;
        width = maxWidth;
    }
    
    if (height > maxHeight) {
        width = (maxHeight / height) * width;
        height = maxHeight;
    }
    
    canvas.width = width;
    canvas.height = height;
    
    ctx.drawImage(img, 0, 0, width, height);
}

/**
 * Draw detection boxes on canvas
 * @param {Image} image - Original image
 * @param {Array} detections - Detection results
 */
export function drawDetections(image, detections) {
    if (!image || !detections) return;
    
    // Redraw the image first
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    
    detections.forEach(detection => {
        const x = detection.bbox.x * canvas.width;
        const y = detection.bbox.y * canvas.height;
        const w = detection.bbox.width * canvas.width;
        const h = detection.bbox.height * canvas.height;
        
        const color = getDetectionColor(detection.type);
        
        // Draw box
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);
        
        // Draw label background
        ctx.fillStyle = color;
        const label = `${detection.label} ${(detection.confidence * 100).toFixed(0)}%`;
        ctx.font = 'bold 14px Inter';
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x, y - 24, textWidth + 16, 24);
        
        // Draw label text
        ctx.fillStyle = 'white';
        ctx.fillText(label, x + 8, y - 7);
    });
}

/**
 * Get color for detection type
 * @param {string} type - Detection type
 * @returns {string} Color code
 */
function getDetectionColor(type) {
    const colors = {
        'signature': '#8b5cf6',
        'stamp': '#ec4899',
        'qr-code': '#06b6d4'
    };
    return colors[type] || '#ffffff';
}

/**
 * Clear canvas
 */
export function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

export { canvas, ctx };
