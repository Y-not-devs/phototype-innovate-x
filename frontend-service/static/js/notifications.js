/**
 * Notification System Module
 * Enhanced toast notification system with multiple types and queue management
 */

const notificationQueue = [];
let isShowingNotification = false;
const MAX_NOTIFICATIONS = 3;

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Notification type (success/error/info/warning)
 * @param {number} duration - Duration in milliseconds (default 5000)
 * @param {Object} options - Additional options {title, action}
 */
export function showNotification(message, type = 'success', duration = 5000, options = {}) {
    const notification = createNotification(message, type, duration, options);
    addToQueue(notification);
    processQueue();
}

/**
 * Show info notification
 * @param {string} message - Message to display
 * @param {number} duration - Duration in milliseconds
 */
export function showInfo(message, duration = 4000) {
    showNotification(message, 'info', duration);
}

/**
 * Show warning notification
 * @param {string} message - Message to display
 * @param {number} duration - Duration in milliseconds
 */
export function showWarning(message, duration = 5000) {
    showNotification(message, 'warning', duration);
}

/**
 * Show success notification
 * @param {string} message - Message to display
 * @param {number} duration - Duration in milliseconds
 */
export function showSuccess(message, duration = 4000) {
    showNotification(message, 'success', duration);
}

/**
 * Show error notification
 * @param {string} message - Message to display
 * @param {number} duration - Duration in milliseconds
 */
export function showError(message, duration = 6000) {
    showNotification(message, 'error', duration);
}

/**
 * Create notification element
 */
function createNotification(message, type, duration, options) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    };
    
    const icon = icons[type] || icons.info;
    const title = options.title || getDefaultTitle(type);
    
    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            ${title ? `<div class="notification-title">${title}</div>` : ''}
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close" aria-label="Close notification">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
    `;
    
    // Close button handler
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => removeNotification(notification));
    
    // Store duration for auto-removal
    notification.dataset.duration = duration;
    
    return notification;
}

/**
 * Get default title based on type
 */
function getDefaultTitle(type) {
    const titles = {
        success: '✓ Success',
        error: '✕ Error',
        warning: '⚠ Warning',
        info: 'ℹ Info'
    };
    return titles[type] || '';
}

/**
 * Add notification to queue
 */
function addToQueue(notification) {
    notificationQueue.push(notification);
}

/**
 * Process notification queue
 */
function processQueue() {
    if (isShowingNotification || notificationQueue.length === 0) {
        return;
    }
    
    // Check how many notifications are currently shown
    const currentNotifications = document.querySelectorAll('.notification.show').length;
    if (currentNotifications >= MAX_NOTIFICATIONS) {
        return;
    }
    
    isShowingNotification = true;
    const notification = notificationQueue.shift();
    displayNotification(notification);
}

/**
 * Display notification
 */
function displayNotification(notification) {
    const container = getNotificationContainer();
    container.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
        isShowingNotification = false;
        processQueue(); // Process next in queue
    }, 50);
    
    // Auto remove
    const duration = parseInt(notification.dataset.duration) || 5000;
    setTimeout(() => {
        removeNotification(notification);
    }, duration);
}

/**
 * Remove notification
 */
function removeNotification(notification) {
    notification.classList.add('hide');
    notification.classList.remove('show');
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
        processQueue(); // Process next in queue
    }, 300);
}

/**
 * Get or create notification container
 */
function getNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}
