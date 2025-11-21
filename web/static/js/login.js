// Login page JavaScript logic
// Handles user authentication and redirects to appropriate dashboard

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const loadingMessage = document.getElementById('loadingMessage');
    const submitButton = loginForm.querySelector('button[type="submit"]');
    
    // Add input validation
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    usernameInput.addEventListener('blur', function() {
        if (this.value.trim()) {
            setFieldSuccess('username');
        }
    });
    
    passwordInput.addEventListener('blur', function() {
        if (this.value) {
            setFieldSuccess('password');
        }
    });
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide any previous messages
        errorMessage.style.display = 'none';
        loadingMessage.style.display = 'block';
        
        // Set button to loading state
        setButtonLoading(submitButton, true);
        
        // Get form data
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        
        // Validate inputs
        if (!username || !password) {
            showError('Please enter both username and password');
            loadingMessage.style.display = 'none';
            setButtonLoading(submitButton, false);
            
            if (!username) {
                setFieldError('username', 'Username is required');
            }
            if (!password) {
                setFieldError('password', 'Password is required');
            }
            return;
        }
        
        try {
            // Call login API
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            const data = await response.json();
            loadingMessage.style.display = 'none';
            setButtonLoading(submitButton, false);
            
            if (data.success) {
                // Store user data in sessionStorage
                sessionStorage.setItem('userEmail', data.email);
                sessionStorage.setItem('userRole', data.role);
                
                // Show success toast
                if (typeof Toast !== 'undefined') {
                    Toast.success('Login successful! Redirecting...');
                }
                
                // Redirect based on role
                setTimeout(() => {
                    if (data.role === 'admin') {
                        window.location.href = '/admin-dashboard';
                    } else {
                        window.location.href = '/dashboard';
                    }
                }, 500);
            } else {
                showError(data.message || 'Invalid username or password');
                setFieldError('username', '');
                setFieldError('password', '');
            }
        } catch (error) {
            loadingMessage.style.display = 'none';
            setButtonLoading(submitButton, false);
            showError('An error occurred during login. Please try again.');
            console.error('Login error:', error);
        }
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    // Clear errors when typing
    usernameInput.addEventListener('input', function() {
        clearFieldValidation('username');
        if (errorMessage.style.display === 'block') {
            errorMessage.style.display = 'none';
        }
    });
    
    passwordInput.addEventListener('input', function() {
        clearFieldValidation('password');
        if (errorMessage.style.display === 'block') {
            errorMessage.style.display = 'none';
        }
    });
});
