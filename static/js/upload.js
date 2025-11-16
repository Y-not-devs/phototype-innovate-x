/**
 * File Upload Module
 * Handles file selection, drag-and-drop, and image preview
 */

import { setCurrentImage, setCurrentFile } from './state.js';
import { displayImage } from './canvas.js';

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const imagePreview = document.getElementById('imagePreview');
const chooseFileBtn = document.getElementById('chooseFileBtn');

/**
 * Initialize upload handlers
 */
export function initUploadHandlers() {
    chooseFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', (e) => {
        if (e.target !== chooseFileBtn && !chooseFileBtn.contains(e.target)) {
            fileInput.click();
        }
    });

    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileInputChange);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    // Only remove drag-over if we're actually leaving the upload area
    if (e.target === uploadArea) {
        uploadArea.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

function handleFileInputChange(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
}

/**
 * Handle file selection
 * @param {File} file - Selected file
 */
export function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }

    setCurrentFile(file);

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            setCurrentImage(img);
            displayImage(img);
            uploadArea.style.display = 'none';
            imagePreview.classList.add('active');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}
