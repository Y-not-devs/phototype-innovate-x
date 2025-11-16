/**
 * Statistics Dashboard Module
 * Handles calculation and visualization of detection statistics
 */

import { state } from './state.js';

const statisticsDashboard = document.getElementById('statisticsDashboard');
let processingStartTime = 0;
let processingEndTime = 0;

/**
 * Initialize statistics tracking
 */
export function initStatistics() {
    // Statistics will be shown after analysis
}

/**
 * Start tracking processing time
 */
export function startProcessingTimer() {
    processingStartTime = performance.now();
}

/**
 * Stop tracking processing time
 */
export function stopProcessingTimer() {
    processingEndTime = performance.now();
}

/**
 * Show statistics dashboard with analysis data
 */
export function showStatistics() {
    const detections = state.detectionResults;
    
    if (!detections || detections.length === 0) {
        hideStatistics();
        return;
    }

    // Calculate statistics
    const stats = calculateStatistics(detections);
    
    // Update stat cards
    updateStatCards(stats);
    
    // Render charts
    renderDistributionChart(stats.distribution);
    renderConfidenceChart(stats.confidenceLevels);
    
    // Show dashboard
    statisticsDashboard.classList.add('active');
}

/**
 * Hide statistics dashboard
 */
export function hideStatistics() {
    statisticsDashboard.classList.remove('active');
}

/**
 * Calculate statistics from detections
 * @param {Array} detections - Detection results
 * @returns {Object} Statistics object
 */
function calculateStatistics(detections) {
    const stats = {
        total: detections.length,
        byType: {
            signature: 0,
            stamp: 0,
            qr_code: 0
        },
        coverage: 0,
        avgConfidence: 0,
        processingTime: Math.round(processingEndTime - processingStartTime),
        distribution: [],
        confidenceLevels: {
            high: 0,
            medium: 0,
            low: 0
        }
    };

    // Count by type and calculate confidence
    let totalConfidence = 0;
    let totalArea = 0;
    
    detections.forEach(detection => {
        // Count by type
        if (detection.type === 'signature') stats.byType.signature++;
        else if (detection.type === 'stamp') stats.byType.stamp++;
        else if (detection.type === 'qr_code') stats.byType.qr_code++;
        
        // Calculate area (simplified)
        const width = detection.bbox[2] - detection.bbox[0];
        const height = detection.bbox[3] - detection.bbox[1];
        totalArea += width * height;
        
        // Sum confidence
        totalConfidence += detection.confidence;
        
        // Categorize confidence
        if (detection.confidence >= 85) stats.confidenceLevels.high++;
        else if (detection.confidence >= 70) stats.confidenceLevels.medium++;
        else stats.confidenceLevels.low++;
    });

    // Calculate averages
    stats.avgConfidence = Math.round(totalConfidence / detections.length);
    
    // Calculate coverage (assuming canvas dimensions from state)
    if (state.currentImage) {
        const canvasArea = state.currentImage.width * state.currentImage.height;
        stats.coverage = Math.round((totalArea / canvasArea) * 100);
    }

    // Prepare distribution data
    stats.distribution = [
        { label: 'Signatures', count: stats.byType.signature, color: 'signature-bar' },
        { label: 'Stamps', count: stats.byType.stamp, color: 'stamp-bar' },
        { label: 'QR Codes', count: stats.byType.qr_code, color: 'qr-bar' }
    ];

    return stats;
}

/**
 * Update stat cards with calculated values
 * @param {Object} stats - Statistics object
 */
function updateStatCards(stats) {
    // Total detections
    const totalEl = document.getElementById('totalDetections');
    animateValue(totalEl, 0, stats.total, 1000);

    // Coverage
    const coverageEl = document.getElementById('coveragePercent');
    animateValue(coverageEl, 0, stats.coverage, 1000, '%');

    // Average confidence
    const confidenceEl = document.getElementById('avgConfidence');
    animateValue(confidenceEl, 0, stats.avgConfidence, 1000, '%');

    // Processing time
    const timeEl = document.getElementById('processingTime');
    animateValue(timeEl, 0, stats.processingTime, 800, 'ms');
}

/**
 * Animate value change
 * @param {HTMLElement} element - Target element
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} duration - Animation duration
 * @param {string} suffix - Value suffix (%, ms, etc)
 */
function animateValue(element, start, end, duration, suffix = '') {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuad = 1 - (1 - progress) * (1 - progress);
        const current = Math.round(start + (end - start) * easeOutQuad);
        
        element.textContent = current + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Render distribution bar chart
 * @param {Array} distribution - Distribution data
 */
function renderDistributionChart(distribution) {
    const container = document.getElementById('distributionChart');
    container.innerHTML = '';

    const maxCount = Math.max(...distribution.map(d => d.count));

    distribution.forEach((item, index) => {
        const barItem = document.createElement('div');
        barItem.className = 'bar-item';
        
        const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
        
        barItem.innerHTML = `
            <div class="bar-label">${item.label}</div>
            <div class="bar-container">
                <div class="bar-fill ${item.color}" style="width: 0%">
                    ${item.count}
                </div>
            </div>
        `;
        
        container.appendChild(barItem);
        
        // Animate bars with delay
        setTimeout(() => {
            const barFill = barItem.querySelector('.bar-fill');
            barFill.style.width = percentage + '%';
        }, 100 + (index * 150));
    });
}

/**
 * Render confidence donut chart
 * @param {Object} confidenceLevels - Confidence level counts
 */
function renderConfidenceChart(confidenceLevels) {
    const container = document.getElementById('confidenceChart');
    container.innerHTML = '';

    const total = confidenceLevels.high + confidenceLevels.medium + confidenceLevels.low;
    
    if (total === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No data available</p>';
        return;
    }

    // Calculate percentages
    const data = [
        { label: 'High (≥85%)', value: confidenceLevels.high, color: '#43e97b', percentage: (confidenceLevels.high / total) * 100 },
        { label: 'Medium (70-84%)', value: confidenceLevels.medium, color: '#4facfe', percentage: (confidenceLevels.medium / total) * 100 },
        { label: 'Low (<70%)', value: confidenceLevels.low, color: '#f5576c', percentage: (confidenceLevels.low / total) * 100 }
    ];

    // Create SVG donut chart
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'donut-svg');
    svg.setAttribute('viewBox', '0 0 200 200');

    const radius = 80;
    const centerX = 100;
    const centerY = 100;
    const strokeWidth = 30;

    let currentAngle = 0;

    data.forEach((item, index) => {
        if (item.value === 0) return;

        const angle = (item.percentage / 100) * 360;
        const largeArcFlag = angle > 180 ? 1 : 0;

        const startX = centerX + radius * Math.cos((currentAngle * Math.PI) / 180);
        const startY = centerY + radius * Math.sin((currentAngle * Math.PI) / 180);

        const endAngle = currentAngle + angle;
        const endX = centerX + radius * Math.cos((endAngle * Math.PI) / 180);
        const endY = centerY + radius * Math.sin((endAngle * Math.PI) / 180);

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const pathData = [
            `M ${startX} ${startY}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`
        ].join(' ');

        path.setAttribute('d', pathData);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', item.color);
        path.setAttribute('stroke-width', strokeWidth);
        path.setAttribute('class', 'donut-segment');
        path.setAttribute('data-index', index);

        svg.appendChild(path);

        currentAngle = endAngle;
    });

    container.appendChild(svg);

    // Create legend
    const legend = document.createElement('div');
    legend.className = 'donut-legend';

    data.forEach((item) => {
        if (item.value === 0) return;

        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <div class="legend-label">
                <div class="legend-color" style="background: ${item.color}"></div>
                <span>${item.label}</span>
            </div>
            <div class="legend-value">${item.value} (${Math.round(item.percentage)}%)</div>
        `;
        legend.appendChild(legendItem);
    });

    container.appendChild(legend);
}
