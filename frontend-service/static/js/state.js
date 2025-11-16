/**
 * Application State Management
 * Central store for application data
 */

export const state = {
    currentImage: null,
    currentFile: null,
    detectionResults: null
};

export function setCurrentImage(image) {
    state.currentImage = image;
}

export function setCurrentFile(file) {
    state.currentFile = file;
}

export function setDetectionResults(results) {
    state.detectionResults = results;
}

export function resetState() {
    state.currentImage = null;
    state.currentFile = null;
    state.detectionResults = null;
}
