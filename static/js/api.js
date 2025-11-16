/**
 * API Communication Module
 * Handles all API calls to the Flask backend
 */

const API_URL = '/api/analyze';

/**
 * Analyze image using Flask API
 * @param {File} file - Image file to analyze
 * @returns {Promise<Array>} Detection results
 */
export async function analyzeImageWithAPI(file) {
    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            // Convert API data format to display format
            return data.detections.map(d => ({
                type: d.type,
                confidence: d.confidence,
                bbox: d.bounding_box,
                label: d.label
            }));
        } else {
            throw new Error(data.error || 'Analysis error');
        }
    } catch (error) {
        console.error('Error analyzing image:', error);
        throw error;
    }
}
