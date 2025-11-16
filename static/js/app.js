/**
 * Digital Inspector - Main Application
 * Entry point that coordinates all modules
 */

import { state, setDetectionResults, resetState } from './state.js';
import { analyzeImageWithAPI } from './api.js';
import { initUploadHandlers } from './upload.js';
import { drawDetections, clearCanvas } from './canvas.js';
import { showLoadingState, hideLoadingState } from './loading.js';
import { showNotification } from './notifications.js';
import { displayResults } from './results.js';
import { initZoomHandlers } from './zoom.js';
import { initExportHandler } from './export.js';
import { initSmoothScrolling, initScrollAnimations } from './utils.js';
import { initInteractiveOverlay, createInteractiveBoxes, clearInteractiveBoxes } from './interactive.js';
import { initStatistics, startProcessingTimer, stopProcessingTimer, showStatistics, hideStatistics } from './statistics.js';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const imagePreview = document.getElementById('imagePreview');
const resultsSection = document.getElementById('resultsSection');
const resetBtn = document.getElementById('resetBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const fileInput = document.getElementById('fileInput');

// Make state globally accessible for export
window.appState = state;

/**
 * Initialize the application
 */
function init() {
    console.log('🚀 Initializing Digital Inspector...');
    
    // Initialize all modules
    initUploadHandlers();
    initZoomHandlers();
    initExportHandler();
    initInteractiveOverlay();
    initStatistics();
    initSmoothScrolling();
    initScrollAnimations();
    
    // Setup event handlers
    setupEventHandlers();
    
    console.log('✅ Digital Inspector loaded successfully!');
    console.log('📄 Ready to analyze documents.');
}

/**
 * Setup main event handlers
 */
function setupEventHandlers() {
    // Reset button handler
    resetBtn.addEventListener('click', handleReset);
    
    // Analyze button handler
    analyzeBtn.addEventListener('click', handleAnalyze);
}

/**
 * Handle reset action
 */
function handleReset() {
    resetState();
    uploadArea.style.display = 'block';
    imagePreview.classList.remove('active');
    resultsSection.classList.remove('active');
    clearCanvas();
    clearInteractiveBoxes();
    hideStatistics();
    fileInput.value = '';
    
    // Hide preview hint
    const previewHint = document.getElementById('previewHint');
    if (previewHint) {
        previewHint.classList.add('hidden');
    }
}

/**
 * Handle analyze action
 */
async function handleAnalyze() {
    if (!state.currentImage || !state.currentFile) return;
    
    showLoadingState();
    startProcessingTimer();
    
    try {
        // Send image to Flask API
        const detections = await analyzeImageWithAPI(state.currentFile);
        stopProcessingTimer();
        setDetectionResults(detections);
        
        // Display results
        displayResults(detections);
        drawDetections(state.currentImage, detections);
        createInteractiveBoxes(detections);
        
        // Show statistics dashboard
        showStatistics();
        
        // Hide loading and show success
        hideLoadingState(true);
        
        // Show preview hint
        const previewHint = document.getElementById('previewHint');
        if (previewHint) {
            previewHint.classList.remove('hidden');
        }
        
        showNotification(`Analysis complete! Found ${detections.length} detection(s)`, 'success');
        
        // Smooth scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 600);
    } catch (error) {
        console.error('Error:', error);
        stopProcessingTimer();
        hideLoadingState(false);
        showNotification('Error analyzing image. Please try again.', 'error');
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
