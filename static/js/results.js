/**
 * Results Display Module
 * Handles displaying and animating detection results
 */

const resultsSection = document.getElementById('resultsSection');
const resultsDetails = document.getElementById('resultsDetails');

/**
 * Display detection results
 * @param {Array} detections - Detection results
 */
export function displayResults(detections) {
    if (!detections) return;
    
    // Update summary cards
    const signatureCount = detections.filter(d => d.type === 'signature').length;
    const stampCount = detections.filter(d => d.type === 'stamp').length;
    const qrCount = detections.filter(d => d.type === 'qr-code').length;
    
    document.querySelector('#signaturesCard .summary-count').textContent = signatureCount;
    document.querySelector('#stampsCard .summary-count').textContent = stampCount;
    document.querySelector('#qrCodesCard .summary-count').textContent = qrCount;
    
    // Animate counts
    animateCount('#signaturesCard .summary-count', signatureCount);
    animateCount('#stampsCard .summary-count', stampCount);
    animateCount('#qrCodesCard .summary-count', qrCount);
    
    // Display detailed results
    resultsDetails.innerHTML = '';
    
    detections.forEach((detection, index) => {
        const resultItem = createResultItem(detection, index);
        resultsDetails.appendChild(resultItem);
    });
    
    // Show results section
    resultsSection.classList.add('active');
}

/**
 * Create result item element
 * @param {Object} detection - Detection data
 * @param {number} index - Item index
 * @returns {HTMLElement} Result item element
 */
function createResultItem(detection, index) {
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item fade-in';
    resultItem.style.animationDelay = `${index * 0.1}s`;
    
    const { iconClass, iconSvg } = getDetectionIcon(detection.type);
    
    resultItem.innerHTML = `
        <div class="result-icon ${iconClass}">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                ${iconSvg}
            </svg>
        </div>
        <div class="result-content">
            <div class="result-type">${detection.label}</div>
            <div class="result-confidence">
                Confidence: <span class="confidence-badge">${(detection.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="result-coords">
                x: ${detection.bbox.x}, y: ${detection.bbox.y}, 
                w: ${detection.bbox.width}, h: ${detection.bbox.height}
            </div>
        </div>
    `;
    
    return resultItem;
}

/**
 * Get icon for detection type
 * @param {string} type - Detection type
 * @returns {Object} Icon class and SVG
 */
function getDetectionIcon(type) {
    const icons = {
        'signature': {
            iconClass: 'signature-bg',
            iconSvg: '<path d="M3 17l6-6 4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        },
        'stamp': {
            iconClass: 'stamp-bg',
            iconSvg: '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>'
        },
        'qr-code': {
            iconClass: 'qr-bg',
            iconSvg: '<rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/><rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>'
        }
    };
    return icons[type] || icons['signature'];
}

/**
 * Animate count up
 * @param {string} selector - Element selector
 * @param {number} target - Target number
 */
function animateCount(selector, target) {
    const element = document.querySelector(selector);
    const duration = 1000;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}
