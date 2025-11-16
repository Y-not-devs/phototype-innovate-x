/**
 * Loading State Module
 * Handles loading animations and progress indication
 */

const loadingState = document.getElementById('loadingState');
const analyzeBtn = document.getElementById('analyzeBtn');
let progressInterval = null;

/**
 * Show loading state with progress
 */
export function showLoadingState() {
    const imagePreview = document.getElementById('imagePreview');
    imagePreview.classList.remove('active');
    loadingState.classList.add('active');
    
    // Update button state
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add('loading');
    analyzeBtn.innerHTML = `
        <span class="spinner-small"></span>
        <span class="btn-text">Analyzing...</span>
        <span class="progress-text">0%</span>
    `;
    
    // Simulate progress
    let progress = 0;
    const progressBar = document.querySelector('.progress-fill');
    const loadingText = document.querySelector('#loadingState p');
    const progressText = analyzeBtn.querySelector('.progress-text');
    const statusMessages = [
        'Initializing analysis...',
        'Processing image...',
        'Detecting signatures...',
        'Detecting stamps...',
        'Detecting QR codes...',
        'Finalizing results...'
    ];
    
    let messageIndex = 0;
    
    progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        progressBar.style.width = `${progress}%`;
        if (progressText) {
            progressText.textContent = `${Math.floor(progress)}%`;
        }
        
        // Update status message
        if (progress > (messageIndex + 1) * 15 && messageIndex < statusMessages.length - 1) {
            messageIndex++;
            loadingText.textContent = statusMessages[messageIndex];
        }
        
        if (progress >= 90) {
            clearInterval(progressInterval);
        }
    }, 200);
}

/**
 * Hide loading state
 * @param {boolean} success - Whether operation was successful
 */
export function hideLoadingState(success = true) {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    const progressBar = document.querySelector('.progress-fill');
    const progressText = analyzeBtn.querySelector('.progress-text');
    
    // Complete progress
    progressBar.style.width = '100%';
    if (progressText) {
        progressText.textContent = '100%';
    }
    
    // Wait a bit to show completion
    setTimeout(() => {
        const imagePreview = document.getElementById('imagePreview');
        loadingState.classList.remove('active');
        imagePreview.classList.add('active');
        
        // Reset button
        analyzeBtn.disabled = false;
        analyzeBtn.classList.remove('loading');
        analyzeBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Analyze
        `;
        
        // Reset progress bar
        progressBar.style.width = '0%';
    }, 500);
}
