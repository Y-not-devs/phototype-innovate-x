/**
 * Interactive Detection Overlay Module
 * Handles interactive bounding boxes with hover effects and click interactions
 */

import { state } from './state.js';

const canvas = document.getElementById('canvas');
const detectionOverlay = document.createElement('div');
detectionOverlay.id = 'detectionOverlay';
detectionOverlay.className = 'detection-overlay';

let overlayBoxes = [];
let hoveredBox = null;

/**
 * Initialize interactive overlay
 */
export function initInteractiveOverlay() {
    // Insert overlay after canvas
    canvas.parentElement.insertBefore(detectionOverlay, canvas.nextSibling);
    
    // Position overlay to match canvas
    positionOverlay();
    
    // Handle window resize
    window.addEventListener('resize', positionOverlay);
}

/**
 * Create interactive detection boxes
 * @param {Array} detections - Detection results
 */
export function createInteractiveBoxes(detections) {
    if (!detections || detections.length === 0) {
        clearInteractiveBoxes();
        return;
    }
    
    overlayBoxes = detections.map((detection, index) => {
        const box = createDetectionBox(detection, index);
        
        // Add event listeners to each box
        box.element.addEventListener('mouseenter', () => handleBoxHover(box.element));
        box.element.addEventListener('mouseleave', () => handleBoxLeave(box.element));
        box.element.addEventListener('click', (e) => handleBoxClick(box.element, detection, index, e));
        
        detectionOverlay.appendChild(box.element);
        return box;
    });
    
    detectionOverlay.style.display = 'block';
    positionOverlay();
}

/**
 * Create a single detection box element
 * @param {Object} detection - Detection data
 * @param {number} index - Detection index
 * @returns {Object} Box object with element and data
 */
function createDetectionBox(detection, index) {
    const box = document.createElement('div');
    box.className = `detection-box ${detection.type}`;
    box.dataset.index = index;
    box.dataset.type = detection.type;
    
    // Calculate position
    const x = detection.bbox.x * canvas.width;
    const y = detection.bbox.y * canvas.height;
    const w = detection.bbox.width * canvas.width;
    const h = detection.bbox.height * canvas.height;
    
    box.style.left = `${x}px`;
    box.style.top = `${y}px`;
    box.style.width = `${w}px`;
    box.style.height = `${h}px`;
    
    // Create label
    const label = document.createElement('div');
    label.className = `detection-label ${detection.type}`;
    label.innerHTML = `
        <span class="label-type">${detection.label}</span>
        <span class="label-confidence">${(detection.confidence * 100).toFixed(0)}%</span>
    `;
    box.appendChild(label);
    
    // Create info tooltip
    const tooltip = createTooltip(detection, index);
    box.appendChild(tooltip);
    
    // Add corner handles
    addCornerHandles(box);
    
    return {
        element: box,
        detection: detection,
        index: index
    };
}

/**
 * Create tooltip for detection
 * @param {Object} detection - Detection data
 * @param {number} index - Detection index
 * @returns {HTMLElement} Tooltip element
 */
function createTooltip(detection, index) {
    const tooltip = document.createElement('div');
    tooltip.className = 'detection-tooltip';
    
    const typeIcons = {
        'signature': '✍️',
        'stamp': '🔖',
        'qr-code': '📱'
    };
    
    tooltip.innerHTML = `
        <div class="tooltip-header">
            <span class="tooltip-icon">${typeIcons[detection.type] || '📄'}</span>
            <span class="tooltip-title">${detection.label} #${index + 1}</span>
        </div>
        <div class="tooltip-body">
            <div class="tooltip-row">
                <span class="tooltip-key">Confidence:</span>
                <span class="tooltip-value">${(detection.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-key">Position:</span>
                <span class="tooltip-value">x: ${detection.bbox.x.toFixed(3)}, y: ${detection.bbox.y.toFixed(3)}</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-key">Size:</span>
                <span class="tooltip-value">w: ${detection.bbox.width.toFixed(3)}, h: ${detection.bbox.height.toFixed(3)}</span>
            </div>
        </div>
        <div class="tooltip-footer">
            <span class="tooltip-hint">Click to focus</span>
        </div>
    `;
    
    return tooltip;
}

/**
 * Add corner handles to box for visual effect
 * @param {HTMLElement} box - Box element
 */
function addCornerHandles(box) {
    const corners = ['tl', 'tr', 'bl', 'br'];
    corners.forEach(corner => {
        const handle = document.createElement('div');
        handle.className = `corner-handle corner-${corner}`;
        box.appendChild(handle);
    });
}

/**
 * Position overlay to match canvas
 */
function positionOverlay() {
    const canvasRect = canvas.getBoundingClientRect();
    const containerRect = canvas.parentElement.getBoundingClientRect();
    
    detectionOverlay.style.width = `${canvas.width}px`;
    detectionOverlay.style.height = `${canvas.height}px`;
    detectionOverlay.style.left = `${canvasRect.left - containerRect.left}px`;
    detectionOverlay.style.top = `${canvasRect.top - containerRect.top}px`;
}

/**
 * Handle box hover
 * @param {HTMLElement} box - Box element
 */
function handleBoxHover(box) {
    if (hoveredBox && hoveredBox !== box) {
        hoveredBox.classList.remove('hovered');
    }
    box.classList.add('hovered');
    hoveredBox = box;
}

/**
 * Handle box leave
 * @param {HTMLElement} box - Box element
 */
function handleBoxLeave(box) {
    box.classList.remove('hovered');
    if (hoveredBox === box) {
        hoveredBox = null;
    }
}

/**
 * Handle box click
 * @param {HTMLElement} box - Box element
 * @param {Object} detection - Detection data
 * @param {number} index - Detection index
 * @param {MouseEvent} e - Mouse event
 */
function handleBoxClick(box, detection, index, e) {
    e.stopPropagation(); // Prevent canvas click from firing
    
    // Add active class
    overlayBoxes.forEach(boxData => boxData.element.classList.remove('active'));
    box.classList.add('active');
    
    // Show detail panel
    showDetectionDetail(detection, index);
    
    // Animate focus
    animateFocus(box);
}

/**
 * Show detection detail panel
 * @param {Object} detection - Detection data
 * @param {number} index - Detection index
 */
function showDetectionDetail(detection, index) {
    // Find or create detail panel
    let detailPanel = document.getElementById('detectionDetailPanel');
    
    if (!detailPanel) {
        detailPanel = document.createElement('div');
        detailPanel.id = 'detectionDetailPanel';
        detailPanel.className = 'detection-detail-panel';
        document.body.appendChild(detailPanel);
    }
    
    const typeIcons = {
        'signature': '✍️',
        'stamp': '🔖',
        'qr-code': '📱'
    };
    
    detailPanel.innerHTML = `
        <div class="detail-panel-header">
            <div class="detail-panel-title">
                <span class="detail-icon">${typeIcons[detection.type] || '📄'}</span>
                <span>${detection.label} #${index + 1}</span>
            </div>
            <button class="detail-panel-close" onclick="this.parentElement.parentElement.classList.remove('active')">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                    <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                </svg>
            </button>
        </div>
        <div class="detail-panel-body">
            <div class="detail-section">
                <h4>Detection Information</h4>
                <div class="detail-info-grid">
                    <div class="detail-info-item">
                        <span class="info-label">Type:</span>
                        <span class="info-value">${detection.label}</span>
                    </div>
                    <div class="detail-info-item">
                        <span class="info-label">Confidence:</span>
                        <span class="info-value confidence-${getConfidenceClass(detection.confidence)}">${(detection.confidence * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            <div class="detail-section">
                <h4>Bounding Box Coordinates</h4>
                <div class="detail-info-grid">
                    <div class="detail-info-item">
                        <span class="info-label">X Position:</span>
                        <span class="info-value">${detection.bbox.x.toFixed(4)}</span>
                    </div>
                    <div class="detail-info-item">
                        <span class="info-label">Y Position:</span>
                        <span class="info-value">${detection.bbox.y.toFixed(4)}</span>
                    </div>
                    <div class="detail-info-item">
                        <span class="info-label">Width:</span>
                        <span class="info-value">${detection.bbox.width.toFixed(4)}</span>
                    </div>
                    <div class="detail-info-item">
                        <span class="info-label">Height:</span>
                        <span class="info-value">${detection.bbox.height.toFixed(4)}</span>
                    </div>
                </div>
            </div>
            <div class="detail-section">
                <h4>Pixel Dimensions</h4>
                <div class="detail-info-grid">
                    <div class="detail-info-item">
                        <span class="info-label">Width:</span>
                        <span class="info-value">${Math.round(detection.bbox.width * canvas.width)}px</span>
                    </div>
                    <div class="detail-info-item">
                        <span class="info-label">Height:</span>
                        <span class="info-value">${Math.round(detection.bbox.height * canvas.height)}px</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    detailPanel.classList.add('active');
}

/**
 * Get confidence class for styling
 * @param {number} confidence - Confidence value
 * @returns {string} Class name
 */
function getConfidenceClass(confidence) {
    if (confidence >= 0.9) return 'high';
    if (confidence >= 0.7) return 'medium';
    return 'low';
}

/**
 * Animate focus on box
 * @param {HTMLElement} box - Box element
 */
function animateFocus(box) {
    box.style.animation = 'none';
    setTimeout(() => {
        box.style.animation = 'pulse 0.6s ease-out';
    }, 10);
}

/**
 * Clear interactive boxes
 */
export function clearInteractiveBoxes() {
    detectionOverlay.innerHTML = '';
    detectionOverlay.style.display = 'none';
    overlayBoxes = [];
    hoveredBox = null;
    
    // Remove detail panel
    const detailPanel = document.getElementById('detectionDetailPanel');
    if (detailPanel) {
        detailPanel.remove();
    }
}

/**
 * Toggle overlay visibility
 * @param {boolean} visible - Whether to show overlay
 */
export function toggleOverlay(visible) {
    detectionOverlay.style.display = visible ? 'block' : 'none';
}
