/**
 * Notification System Component
 * Display toast notifications and alerts for user feedback
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container if doesn't exist
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                pointer-events: none;
            `;
            document.body.appendChild(container);
            this.container = container;
        } else {
            this.container = document.getElementById('notificationContainer');
        }
    }

    /**
     * Show success notification
     */
    success(message, duration = 4000) {
        this.show(message, 'success', duration);
    }

    /**
     * Show error notification
     */
    error(message, duration = 6000) {
        this.show(message, 'error', duration);
    }

    /**
     * Show warning notification
     */
    warning(message, duration = 5000) {
        this.show(message, 'warning', duration);
    }

    /**
     * Show info notification
     */
    info(message, duration = 4000) {
        this.show(message, 'info', duration);
    }

    /**
     * Show notification with custom type
     */
    show(message, type = 'info', duration = 4000) {
        const id = 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        const notification = {
            id: id,
            message: message,
            type: type,
            timestamp: Date.now()
        };

        this.notifications.push(notification);
        
        // Create notification element
        const notifEl = this.createNotificationElement(notification);
        this.container.appendChild(notifEl);

        // Trigger animation
        setTimeout(() => {
            notifEl.classList.add('show');
        }, 10);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, duration);
        }

        return id;
    }

    createNotificationElement(notification) {
        const el = document.createElement('div');
        el.id = notification.id;
        el.className = `notification notification-${notification.type}`;
        
        // Get icon and colors based on type
        const config = this.getNotificationConfig(notification.type);
        
        el.style.cssText = `
            background: ${config.background};
            color: ${config.color};
            border-left: 4px solid ${config.borderColor};
            padding: 16px 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: flex-start;
            gap: 12px;
            opacity: 0;
            transform: translateX(400px);
            transition: all 0.3s ease;
            pointer-events: all;
            max-width: 400px;
            word-wrap: break-word;
        `;

        el.innerHTML = `
            <div style="font-size: 20px; flex-shrink: 0; margin-top: 2px;">
                ${config.icon}
            </div>
            <div style="flex: 1; font-size: 14px; line-height: 1.5;">
                ${this.escapeHtml(notification.message)}
            </div>
            <button onclick="notificationSystem.dismiss('${notification.id}')" 
                    style="background: none; border: none; color: inherit; cursor: pointer; font-size: 20px; padding: 0; opacity: 0.6; flex-shrink: 0; line-height: 1;"
                    onmouseover="this.style.opacity='1'" 
                    onmouseout="this.style.opacity='0.6'">
                ×
            </button>
        `;

        return el;
    }

    getNotificationConfig(type) {
        const configs = {
            success: {
                icon: '✅',
                background: '#d4edda',
                color: '#155724',
                borderColor: '#28a745'
            },
            error: {
                icon: '❌',
                background: '#f8d7da',
                color: '#721c24',
                borderColor: '#dc3545'
            },
            warning: {
                icon: '⚠️',
                background: '#fff3cd',
                color: '#856404',
                borderColor: '#ffc107'
            },
            info: {
                icon: 'ℹ️',
                background: '#d1ecf1',
                color: '#0c5460',
                borderColor: '#17a2b8'
            }
        };

        return configs[type] || configs.info;
    }

    /**
     * Dismiss notification
     */
    dismiss(id) {
        const el = document.getElementById(id);
        if (!el) return;

        // Animate out
        el.style.opacity = '0';
        el.style.transform = 'translateX(400px)';

        // Remove after animation
        setTimeout(() => {
            if (el.parentNode) {
                el.parentNode.removeChild(el);
            }
            
            // Remove from array
            this.notifications = this.notifications.filter(n => n.id !== id);
        }, 300);
    }

    /**
     * Dismiss all notifications
     */
    dismissAll() {
        this.notifications.forEach(notification => {
            this.dismiss(notification.id);
        });
    }

    /**
     * Confirm dialog (replaces window.confirm)
     */
    confirm(message, onConfirm, onCancel) {
        const modalId = 'confirmModal_' + Date.now();
        
        const modalHTML = `
            <div id="${modalId}" class="modal" style="display: block;">
                <div class="modal-content" style="max-width: 450px; animation: modalSlideIn 0.3s ease;">
                    <div class="modal-header" style="background: #ff9800; color: white;">
                        <h3 style="margin: 0;">⚠️ Confirmation Required</h3>
                    </div>
                    <div class="modal-body">
                        <p style="font-size: 16px; line-height: 1.6; margin: 20px 0;">
                            ${this.escapeHtml(message)}
                        </p>
                    </div>
                    <div style="padding: 20px; display: flex; gap: 10px; justify-content: flex-end; border-top: 1px solid #eee;">
                        <button onclick="notificationSystem.handleConfirmCancel('${modalId}', ${!!onCancel})" 
                                class="btn-secondary">
                            Cancel
                        </button>
                        <button onclick="notificationSystem.handleConfirmOk('${modalId}')" 
                                class="btn-primary">
                            Confirm
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Store callbacks
        window[`confirm_${modalId}_ok`] = onConfirm;
        window[`confirm_${modalId}_cancel`] = onCancel;
    }

    handleConfirmOk(modalId) {
        const callback = window[`confirm_${modalId}_ok`];
        if (callback) callback();
        
        this.removeConfirmModal(modalId);
    }

    handleConfirmCancel(modalId, hasCallback) {
        if (hasCallback) {
            const callback = window[`confirm_${modalId}_cancel`];
            if (callback) callback();
        }
        
        this.removeConfirmModal(modalId);
    }

    removeConfirmModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.remove();
        }
        
        // Clean up callbacks
        delete window[`confirm_${modalId}_ok`];
        delete window[`confirm_${modalId}_cancel`];
    }

    /**
     * Show loading notification (doesn't auto-dismiss)
     */
    loading(message = 'Loading...') {
        const id = this.show(`⏳ ${message}`, 'info', 0);
        return id; // Return id so caller can dismiss later
    }

    /**
     * Show progress notification
     */
    progress(message, current, total) {
        const percentage = Math.round((current / total) * 100);
        const progressBar = `
            <div style="margin-top: 8px;">
                <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #667eea; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
                <div style="margin-top: 4px; font-size: 12px; opacity: 0.8;">
                    ${current} of ${total} (${percentage}%)
                </div>
            </div>
        `;
        
        // For now, just show as info (can be enhanced to update existing notification)
        this.info(`${message}${progressBar}`, 0);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .notification.show {
        opacity: 1 !important;
        transform: translateX(0) !important;
    }

    @keyframes modalSlideIn {
        from {
            opacity: 0;
            transform: translateY(-50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Create global instance
const notificationSystem = new NotificationSystem();

// Add convenience global functions
function showSuccess(message) {
    notificationSystem.success(message);
}

function showError(message) {
    notificationSystem.error(message);
}

function showWarning(message) {
    notificationSystem.warning(message);
}

function showInfo(message) {
    notificationSystem.info(message);
}

function showLoading(message) {
    return notificationSystem.loading(message);
}

function showConfirm(message, onConfirm, onCancel) {
    notificationSystem.confirm(message, onConfirm, onCancel);
}
