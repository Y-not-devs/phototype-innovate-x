/**
 * Export Module
 * Handles exporting detection results to JSON
 */

import { showSuccess, showInfo } from './notifications.js';

const exportBtn = document.getElementById('exportBtn');
const canvas = document.getElementById('canvas');

/**
 * Initialize export handler
 */
export function initExportHandler() {
    exportBtn.addEventListener('click', handleExport);
}

/**
 * Export detection results to JSON file
 * @param {Array} detections - Detection results
 */
function handleExport() {
    const detectionResults = window.appState?.detectionResults;
    if (!detectionResults) return;
    
    const exportData = {
        timestamp: new Date().toISOString(),
        image_dimensions: {
            width: canvas.width,
            height: canvas.height
        },
        detections: detectionResults.map(d => ({
            type: d.type,
            label: d.label,
            confidence: parseFloat(d.confidence),
            bounding_box: {
                x: d.bbox.x,
                y: d.bbox.y,
                width: d.bbox.width,
                height: d.bbox.height
            }
        })),
        summary: {
            total_detections: detectionResults.length,
            signatures: detectionResults.filter(d => d.type === 'signature').length,
            stamps: detectionResults.filter(d => d.type === 'stamp').length,
            qr_codes: detectionResults.filter(d => d.type === 'qr-code').length
        }
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    const filename = `detection_results_${Date.now()}.json`;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    
    // Show success notification
    showSuccess(`Export successful! Downloaded "${filename}"`, 5000);
}
