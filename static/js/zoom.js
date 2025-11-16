/**
 * Image Zoom & Pan Module
 * Handles full-screen image preview with zoom and pan functionality
 */

import { state } from './state.js';

// Modal Elements
const imagePreviewModal = document.getElementById('imagePreviewModal');
const closeModalBtn = document.getElementById('closeModal');
const zoomCanvas = document.getElementById('zoomCanvas');
const zoomCtx = zoomCanvas.getContext('2d');
const zoomContainer = document.getElementById('zoomContainer');
const zoomLevelText = document.getElementById('zoomLevelText');

// Zoom Controls
const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const resetZoomBtn = document.getElementById('resetZoomBtn');
const fitToScreenBtn = document.getElementById('fitToScreenBtn');

// Zoom State
const zoomState = {
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    startX: 0,
    startY: 0,
    minScale: 0.1,
    maxScale: 5
};

/**
 * Initialize zoom modal handlers
 */
export function initZoomHandlers() {
    const canvas = document.getElementById('canvas');
    const imagePreview = document.getElementById('imagePreview');
    
    // Canvas click to open modal
    canvas.addEventListener('click', (e) => {
        if (state.currentImage && state.detectionResults) {
            openImagePreview();
        }
    });

    // Add click handler to image preview container to catch clicks outside boxes
    imagePreview.addEventListener('click', (e) => {
        // Check if click is on canvas or empty space
        if (e.target === canvas || e.target === imagePreview) {
            if (state.currentImage && state.detectionResults) {
                openImagePreview();
            }
        }
    });

    // Hover effects
    canvas.addEventListener('mouseenter', () => {
        if (state.currentImage && state.detectionResults) {
            canvas.style.cursor = 'zoom-in';
            canvas.style.opacity = '0.95';
        }
    });

    canvas.addEventListener('mouseleave', () => {
        canvas.style.cursor = 'default';
        canvas.style.opacity = '1';
    });

    // Modal controls
    closeModalBtn.addEventListener('click', closeImagePreview);
    imagePreviewModal.addEventListener('click', (e) => {
        if (e.target === imagePreviewModal) closeImagePreview();
    });

    // Zoom buttons
    zoomInBtn.addEventListener('click', () => zoom(1.2));
    zoomOutBtn.addEventListener('click', () => zoom(0.8));
    resetZoomBtn.addEventListener('click', resetZoom);
    fitToScreenBtn.addEventListener('click', fitToScreen);

    // Mouse interactions
    zoomCanvas.addEventListener('wheel', handleWheel);
    zoomCanvas.addEventListener('mousedown', handleMouseDown);
    zoomCanvas.addEventListener('mousemove', handleMouseMove);
    zoomCanvas.addEventListener('mouseup', handleMouseUp);
    zoomCanvas.addEventListener('mouseleave', handleMouseUp);

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyDown);
    
    // Set initial cursor
    zoomCanvas.style.cursor = 'grab';
}

function openImagePreview() {
    imagePreviewModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    const containerWidth = zoomContainer.clientWidth;
    const containerHeight = zoomContainer.clientHeight;
    
    zoomCanvas.width = containerWidth;
    zoomCanvas.height = containerHeight;
    
    // Calculate initial scale
    const scaleX = containerWidth / state.currentImage.width;
    const scaleY = containerHeight / state.currentImage.height;
    zoomState.scale = Math.min(scaleX, scaleY, 1);
    
    // Center the image
    zoomState.offsetX = (containerWidth - state.currentImage.width * zoomState.scale) / 2;
    zoomState.offsetY = (containerHeight - state.currentImage.height * zoomState.scale) / 2;
    
    renderZoomCanvas();
    updateZoomLevel();
}

function closeImagePreview() {
    imagePreviewModal.classList.remove('active');
    document.body.style.overflow = '';
}

function renderZoomCanvas() {
    zoomCtx.clearRect(0, 0, zoomCanvas.width, zoomCanvas.height);
    zoomCtx.save();
    
    zoomCtx.translate(zoomState.offsetX, zoomState.offsetY);
    zoomCtx.scale(zoomState.scale, zoomState.scale);
    
    zoomCtx.drawImage(state.currentImage, 0, 0);
    
    // Draw detections
    if (state.detectionResults) {
        state.detectionResults.forEach(detection => {
            const x = detection.bbox.x * state.currentImage.width;
            const y = detection.bbox.y * state.currentImage.height;
            const w = detection.bbox.width * state.currentImage.width;
            const h = detection.bbox.height * state.currentImage.height;
            
            const color = getDetectionColor(detection.type);
            
            zoomCtx.strokeStyle = color;
            zoomCtx.lineWidth = 3 / zoomState.scale;
            zoomCtx.shadowColor = color;
            zoomCtx.shadowBlur = 10 / zoomState.scale;
            zoomCtx.strokeRect(x, y, w, h);
            
            zoomCtx.shadowBlur = 0;
            zoomCtx.fillStyle = color;
            const label = `${detection.label} ${(detection.confidence * 100).toFixed(0)}%`;
            zoomCtx.font = `bold ${14 / zoomState.scale}px Inter`;
            const textWidth = zoomCtx.measureText(label).width;
            zoomCtx.fillRect(x, y - 24 / zoomState.scale, textWidth + 16 / zoomState.scale, 24 / zoomState.scale);
            
            zoomCtx.fillStyle = 'white';
            zoomCtx.fillText(label, x + 8 / zoomState.scale, y - 7 / zoomState.scale);
        });
    }
    
    zoomCtx.restore();
}

function getDetectionColor(type) {
    const colors = {
        'signature': '#a78bfa',
        'stamp': '#f472b6',
        'qr-code': '#22d3ee'
    };
    return colors[type] || '#ffffff';
}

function updateZoomLevel() {
    const percentage = Math.round(zoomState.scale * 100);
    zoomLevelText.textContent = `${percentage}%`;
}

function zoom(delta) {
    const oldScale = zoomState.scale;
    zoomState.scale *= delta;
    zoomState.scale = Math.max(zoomState.minScale, Math.min(zoomState.maxScale, zoomState.scale));
    
    const centerX = zoomCanvas.width / 2;
    const centerY = zoomCanvas.height / 2;
    
    zoomState.offsetX = centerX - (centerX - zoomState.offsetX) * (zoomState.scale / oldScale);
    zoomState.offsetY = centerY - (centerY - zoomState.offsetY) * (zoomState.scale / oldScale);
    
    renderZoomCanvas();
    updateZoomLevel();
}

function resetZoom() {
    const containerWidth = zoomContainer.clientWidth;
    const containerHeight = zoomContainer.clientHeight;
    
    const scaleX = containerWidth / state.currentImage.width;
    const scaleY = containerHeight / state.currentImage.height;
    zoomState.scale = Math.min(scaleX, scaleY, 1);
    
    zoomState.offsetX = (containerWidth - state.currentImage.width * zoomState.scale) / 2;
    zoomState.offsetY = (containerHeight - state.currentImage.height * zoomState.scale) / 2;
    
    renderZoomCanvas();
    updateZoomLevel();
}

function fitToScreen() {
    const containerWidth = zoomContainer.clientWidth;
    const containerHeight = zoomContainer.clientHeight;
    
    const scaleX = containerWidth / state.currentImage.width;
    const scaleY = containerHeight / state.currentImage.height;
    zoomState.scale = Math.min(scaleX, scaleY);
    
    zoomState.offsetX = (containerWidth - state.currentImage.width * zoomState.scale) / 2;
    zoomState.offsetY = (containerHeight - state.currentImage.height * zoomState.scale) / 2;
    
    renderZoomCanvas();
    updateZoomLevel();
}

function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    zoom(delta);
}

function handleMouseDown(e) {
    zoomState.isDragging = true;
    zoomState.startX = e.clientX - zoomState.offsetX;
    zoomState.startY = e.clientY - zoomState.offsetY;
    zoomCanvas.style.cursor = 'grabbing';
}

function handleMouseMove(e) {
    if (zoomState.isDragging) {
        zoomState.offsetX = e.clientX - zoomState.startX;
        zoomState.offsetY = e.clientY - zoomState.startY;
        renderZoomCanvas();
    }
}

function handleMouseUp() {
    zoomState.isDragging = false;
    zoomCanvas.style.cursor = 'grab';
}

function handleKeyDown(e) {
    if (!imagePreviewModal.classList.contains('active')) return;
    
    switch(e.key) {
        case 'Escape':
            closeImagePreview();
            break;
        case '+':
        case '=':
            zoom(1.2);
            break;
        case '-':
            zoom(0.8);
            break;
        case '0':
            resetZoom();
            break;
        case 'f':
        case 'F':
            fitToScreen();
            break;
    }
}
