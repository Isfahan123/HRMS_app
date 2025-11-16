// Login page JavaScript logic
// Handles user authentication and redirects to appropriate dashboard

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const loadingMessage = document.getElementById('loadingMessage');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide any previous messages
        errorMessage.style.display = 'none';
        loadingMessage.style.display = 'block';
        
        // Get form data
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        // Validate inputs
        if (!username || !password) {
            showError('Please enter both username and password');
            loadingMessage.style.display = 'none';
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
            
            if (data.success) {
                // Store user data in sessionStorage
                sessionStorage.setItem('userEmail', data.email);
                sessionStorage.setItem('userRole', data.role);
                
                // Redirect based on role
                if (data.role === 'admin') {
                    window.location.href = '/admin-dashboard';
                } else {
                    window.location.href = '/dashboard';
                }
            } else {
                showError(data.message || 'Login failed');
            }
        } catch (error) {
            loadingMessage.style.display = 'none';
            showError('An error occurred during login. Please try again.');
            console.error('Login error:', error);
        }
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
});
