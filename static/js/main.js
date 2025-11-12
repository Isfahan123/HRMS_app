// Main JavaScript for HRMS Web Application

// Global utility functions
function showAlert(message, type = 'info') {
    const alertDiv = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    $('.container').first().prepend(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').first().fadeOut(() => {
            $(this).remove();
        });
    }, 5000);
}

// API call wrapper
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showAlert('An error occurred: ' + error.message, 'danger');
        throw error;
    }
}

// Format date helper
function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

// Format time helper
function formatTime(timeString) {
    if (!timeString) return '--';
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Format currency helper
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return 'RM 0.00';
    return 'RM ' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Loading spinner
function showLoading(elementId) {
    const loadingHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading...</p>
        </div>
    `;
    $(`#${elementId}`).html(loadingHTML);
}

function hideLoading(elementId) {
    // Loading will be replaced by content
}

// Confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Profile modal
function viewProfile() {
    // Redirect to dashboard profile tab
    if (window.location.pathname.includes('dashboard')) {
        $('#profile-tab').tab('show');
    } else {
        window.location.href = '/dashboard#profile';
    }
}

// Initialize tooltips
$(document).ready(function() {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// Export functions
window.HRMS = {
    showAlert,
    apiCall,
    formatDate,
    formatTime,
    formatCurrency,
    showLoading,
    hideLoading,
    confirmAction,
    viewProfile
};
