/**
 * UX Utilities for HRMS Application
 * Provides toast notifications, loading states, and other UX enhancements
 */

// Toast Notification System
const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 5000, title = null) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const icon = document.createElement('span');
        icon.className = 'toast-icon';
        icon.textContent = icons[type] || icons.info;

        const content = document.createElement('div');
        content.className = 'toast-content';

        if (title) {
            const titleEl = document.createElement('div');
            titleEl.className = 'toast-title';
            titleEl.textContent = title;
            content.appendChild(titleEl);
        }

        const messageEl = document.createElement('div');
        messageEl.className = 'toast-message';
        messageEl.textContent = message;
        content.appendChild(messageEl);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.textContent = '×';
        closeBtn.setAttribute('aria-label', 'Close notification');
        closeBtn.onclick = () => this.hide(toast);

        toast.appendChild(icon);
        toast.appendChild(content);
        toast.appendChild(closeBtn);

        this.container.appendChild(toast);

        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => this.hide(toast), duration);
        }

        return toast;
    },

    hide(toast) {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    },

    success(message, title = 'Success') {
        return this.show(message, 'success', 5000, title);
    },

    error(message, title = 'Error') {
        return this.show(message, 'error', 7000, title);
    },

    warning(message, title = 'Warning') {
        return this.show(message, 'warning', 6000, title);
    },

    info(message, title = null) {
        return this.show(message, 'info', 5000, title);
    }
};

// Loading Overlay
const LoadingOverlay = {
    overlay: null,

    show(message = 'Loading...') {
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'loading-overlay';
            this.overlay.innerHTML = `
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
            `;
            document.body.appendChild(this.overlay);
        } else {
            this.overlay.querySelector('.loading-text').textContent = message;
            this.overlay.style.display = 'flex';
        }
    },

    hide() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
        }
    }
};

// Button Loading State
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
        button.setAttribute('data-original-text', button.textContent);
    } else {
        button.classList.remove('loading');
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.textContent = originalText;
        }
    }
}

// Form Validation Helpers
function setFieldError(fieldId, errorMessage) {
    const formGroup = document.getElementById(fieldId)?.closest('.form-group');
    if (formGroup) {
        formGroup.classList.add('has-error');
        formGroup.classList.remove('has-success');
        
        let errorEl = formGroup.querySelector('.form-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'form-error';
            formGroup.appendChild(errorEl);
        }
        errorEl.textContent = errorMessage;
    }
}

function setFieldSuccess(fieldId) {
    const formGroup = document.getElementById(fieldId)?.closest('.form-group');
    if (formGroup) {
        formGroup.classList.remove('has-error');
        formGroup.classList.add('has-success');
        
        const errorEl = formGroup.querySelector('.form-error');
        if (errorEl) {
            errorEl.remove();
        }
    }
}

function clearFieldValidation(fieldId) {
    const formGroup = document.getElementById(fieldId)?.closest('.form-group');
    if (formGroup) {
        formGroup.classList.remove('has-error', 'has-success');
        
        const errorEl = formGroup.querySelector('.form-error');
        if (errorEl) {
            errorEl.remove();
        }
    }
}

// Skeleton Screen Helpers
function createSkeletonTable(rows = 5, columns = 5) {
    let html = '<div class="skeleton-table">';
    for (let i = 0; i < rows; i++) {
        html += '<div class="skeleton-table-row">';
        for (let j = 0; j < columns; j++) {
            html += '<div class="skeleton skeleton-table-cell"></div>';
        }
        html += '</div>';
    }
    html += '</div>';
    return html;
}

function showSkeleton(containerId, type = 'table', count = 5) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (type === 'table') {
        container.innerHTML = createSkeletonTable(count);
    } else if (type === 'cards') {
        let html = '<div class="summary-grid">';
        for (let i = 0; i < count; i++) {
            html += '<div class="skeleton skeleton-card"></div>';
        }
        html += '</div>';
        container.innerHTML = html;
    }
}

// Empty State Helper
function showEmptyState(containerId, icon, title, message, actionText = null, actionCallback = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let html = `
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <div class="empty-state-title">${title}</div>
            <div class="empty-state-message">${message}</div>
    `;

    if (actionText && actionCallback) {
        const btnId = `empty-state-action-${Date.now()}`;
        html += `
            <div class="empty-state-action">
                <button id="${btnId}" class="btn-primary">${actionText}</button>
            </div>
        `;
        container.innerHTML = html + '</div>';
        
        document.getElementById(btnId).addEventListener('click', actionCallback);
    } else {
        container.innerHTML = html + '</div>';
    }
}

// Confirm Dialog
function confirm(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        const result = window.confirm(`${title}\n\n${message}`);
        resolve(result);
    });
}

// Debounce Function
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format Currency
function formatCurrency(amount, currency = 'RM') {
    const formatted = parseFloat(amount).toLocaleString('en-MY', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    return `${currency} ${formatted}`;
}

// Format Date
function formatDate(dateString, format = 'dd/mm/yyyy') {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    if (format === 'dd/mm/yyyy') {
        return `${day}/${month}/${year}`;
    } else if (format === 'yyyy-mm-dd') {
        return `${year}-${month}-${day}`;
    }
    return dateString;
}

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.success('Copied to clipboard');
        return true;
    } catch (err) {
        Toast.error('Failed to copy to clipboard');
        return false;
    }
}

// Download CSV
function downloadCSV(data, filename = 'export.csv') {
    const csv = arrayToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
    Toast.success('File downloaded successfully');
}

function arrayToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const rows = data.map(obj => 
        headers.map(header => {
            const value = obj[header] || '';
            // Escape quotes and wrap in quotes if contains comma
            return typeof value === 'string' && (value.includes(',') || value.includes('"'))
                ? `"${value.replace(/"/g, '""')}"`
                : value;
        }).join(',')
    );
    
    return [headers.join(','), ...rows].join('\n');
}

// Keyboard Shortcuts
const KeyboardShortcuts = {
    shortcuts: {},

    register(key, callback, description = '') {
        this.shortcuts[key.toLowerCase()] = { callback, description };
    },

    init() {
        document.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            const ctrl = e.ctrlKey || e.metaKey;
            const alt = e.altKey;
            const shift = e.shiftKey;

            let shortcut = '';
            if (ctrl) shortcut += 'ctrl+';
            if (alt) shortcut += 'alt+';
            if (shift) shortcut += 'shift+';
            shortcut += key;

            if (this.shortcuts[shortcut]) {
                e.preventDefault();
                this.shortcuts[shortcut].callback(e);
            }
        });
    },

    showHelp() {
        const shortcuts = Object.keys(this.shortcuts).map(key => {
            return `${key}: ${this.shortcuts[key].description}`;
        }).join('\n');
        
        alert(`Keyboard Shortcuts:\n\n${shortcuts}`);
    }
};

// Smooth Scroll to Element
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const top = element.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
    }
}

// Auto-save Form Data
const AutoSave = {
    interval: null,
    formId: null,

    start(formId, saveCallback, intervalMs = 30000) {
        this.formId = formId;
        this.stop(); // Clear any existing interval

        this.interval = setInterval(() => {
            const form = document.getElementById(formId);
            if (form) {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                saveCallback(data);
                Toast.info('Draft saved', null);
            }
        }, intervalMs);
    },

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
};

// Export functions to global scope
window.Toast = Toast;
window.LoadingOverlay = LoadingOverlay;
window.setButtonLoading = setButtonLoading;
window.setFieldError = setFieldError;
window.setFieldSuccess = setFieldSuccess;
window.clearFieldValidation = clearFieldValidation;
window.showSkeleton = showSkeleton;
window.showEmptyState = showEmptyState;
window.confirmAction = confirm;
window.debounce = debounce;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;
window.downloadCSV = downloadCSV;
window.KeyboardShortcuts = KeyboardShortcuts;
window.scrollToElement = scrollToElement;
window.AutoSave = AutoSave;

// Initialize keyboard shortcuts on load
document.addEventListener('DOMContentLoaded', () => {
    KeyboardShortcuts.init();
    
    // Register common shortcuts
    KeyboardShortcuts.register('ctrl+s', (e) => {
        e.preventDefault();
        Toast.info('Save shortcut pressed');
    }, 'Save current form');

    KeyboardShortcuts.register('?', () => {
        KeyboardShortcuts.showHelp();
    }, 'Show keyboard shortcuts');
});

console.log('✨ UX utilities loaded successfully');
