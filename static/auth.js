// Auth JavaScript - Handles Signup, Login, and Password Reset (NO OTP VERSION)

document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    const resetPasswordForm = document.getElementById('reset-password-form');

    if (signupForm) signupForm.addEventListener('submit', handleSignup);
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (forgotPasswordForm) forgotPasswordForm.addEventListener('submit', handleForgotPassword);
    if (resetPasswordForm) resetPasswordForm.addEventListener('submit', handleResetPassword);
});

// ==================== SIGNUP ====================

async function handleSignup(e) {
    e.preventDefault();

    const username = document.getElementById('username')?.value.trim();
    const email = document.getElementById('email')?.value.trim();
    const phone = document.getElementById('phone')?.value.trim();
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirm_password')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    if (!username || !email || !password || !confirmPassword) {
        showError('Please fill in all required fields');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Creating Account...';

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, phone, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', 'Account created successfully!');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showError(data.error || data.message || 'Signup failed');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Create Account</span><i class="fa fa-user-plus"></i>';
        }
    } catch (error) {
        console.error('Signup error:', error);
        showError('An error occurred. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Create Account</span><i class="fa fa-user-plus"></i>';
    }
}

// ==================== LOGIN ====================

async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('login-email')?.value || document.getElementById('email')?.value;
    const password = document.getElementById('login-password')?.value || document.getElementById('password')?.value;
    const submitBtn = document.getElementById('login-btn');

    if (!email || !password) {
        showError('Please enter email and password');
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Signing In...';
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', 'Login successful!');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1200);
        } else {
            showError(data.error || 'Invalid credentials');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Sign In</span><i class="fa fa-arrow-right"></i>';
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('An error occurred. Please try again.');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Sign In</span><i class="fa fa-arrow-right"></i>';
        }
    }
}

// ==================== FORGOT PASSWORD ====================

async function handleForgotPassword(e) {
    e.preventDefault();

    const email = document.getElementById('forgot-email')?.value || document.getElementById('email')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    if (!email) {
        showError('Please enter your email address');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending...';

    try {
        const response = await fetch('/api/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', data.message || 'Reset link sent');
            submitBtn.innerHTML = '<i class="fa fa-check"></i> Sent!';
        } else {
            showError(data.error || 'Failed to send reset link');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Send Reset Link';
        }
    } catch (error) {
        console.error(error);
        showError('An error occurred');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Send Reset Link';
    }
}

// ==================== RESET PASSWORD ====================

async function handleResetPassword(e) {
    e.preventDefault();

    const password = document.getElementById('reset-password')?.value;
    const confirmPassword = document.getElementById('reset-confirm-password')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    if (!password || !confirmPassword) {
        showError('Please enter both passwords');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!token) {
        showError('Invalid reset link');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Resetting...';

    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', 'Password reset successfully');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showError(data.error || 'Reset failed');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Reset Password';
        }
    } catch (error) {
        console.error(error);
        showError('An error occurred');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Reset Password';
    }
}

// ==================== UTILITIES ====================

function showError(message, elementId = 'error-message') {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<i class="fa fa-exclamation-circle"></i><span>${message}</span>`;
        el.style.display = 'flex';
    }
}

function showToast(type, message) {
    if (!message) {
        message = type;
        type = 'success';
    }

    const old = document.querySelector('.toast-notification');
    if (old) old.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="fa fa-${type === 'success' ? 'check' : 'times'}"></i>
        </div>
        <div class="toast-content">
            <strong>${type === 'success' ? 'Success' : 'Error'}</strong>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('active'), 50);
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
