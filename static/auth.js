// Auth JavaScript - Handles Signup, Login, and Password Reset (NO OTP)

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

// ==================== SIGNUP FUNCTIONS ====================

async function handleSignup(e) {
    e.preventDefault();
    
    const username = document.getElementById('username')?.value;
    const email = document.getElementById('email')?.value;
    const phone = document.getElementById('phone')?.value;
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirm_password')?.value;
    const submitBtn = e.target?.querySelector('button[type="submit"]');

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

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Creating Account...';
    }

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, phone })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', 'Account created successfully! Redirecting to login...');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showError(data.error || 'Signup failed');
            resetSignupButton(submitBtn);
        }

    } catch (error) {
        console.error('Signup error:', error);
        showError('An error occurred. Please try again.');
        resetSignupButton(submitBtn);
    }
}

function resetSignupButton(btn) {
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>Create Account</span><i class="fa fa-user-plus"></i>';
    }
}

// ==================== LOGIN FUNCTIONS ====================

async function handleLogin(e) {
    e.preventDefault();
    
    const emailInput = document.getElementById('login-email') || document.getElementById('email');
    const passwordInput = document.getElementById('login-password') || document.getElementById('password');
    
    const email = emailInput?.value;
    const password = passwordInput?.value;
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
            setTimeout(() => window.location.href = '/dashboard', 1200);
        } else {
            showError(data.error || 'Invalid credentials');
            resetLoginButton(submitBtn);
        }

    } catch (error) {
        console.error('Login error:', error);
        showError('An error occurred');
        resetLoginButton(submitBtn);
    }
}

function resetLoginButton(btn) {
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>Sign In</span><i class="fa fa-arrow-right"></i>';
    }
}

// ==================== FORGOT PASSWORD ====================

async function handleForgotPassword(e) {
    e.preventDefault();
    
    const email = document.getElementById('forgot-email')?.value || document.getElementById('email')?.value;
    const submitBtn = e.target?.querySelector('button[type="submit"]');

    if (!email) {
        showError('Please enter your email address');
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending...';
    }

    try {
        const response = await fetch('/api/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', data.message || 'Reset link sent');
        } else {
            showError(data.error || 'Failed to send reset link');
        }

    } catch (error) {
        console.error('Forgot password error:', error);
        showError('An error occurred');
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ==================== RESET PASSWORD ====================

async function handleResetPassword(e) {
    e.preventDefault();
    
    const password = document.getElementById('reset-password')?.value;
    const confirmPassword = document.getElementById('reset-confirm-password')?.value;
    const submitBtn = e.target?.querySelector('button[type="submit"]');

    if (!password || !confirmPassword) {
        showError('Please enter both passwords');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    const token = new URLSearchParams(window.location.search).get('token');

    if (!token) {
        showError('Invalid reset link');
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Resetting...';
    }

    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('success', 'Password reset successfully');
            setTimeout(() => window.location.href = '/login', 1500);
        } else {
            showError(data.error || 'Reset failed');
        }

    } catch (error) {
        console.error('Reset password error:', error);
        showError('An error occurred');
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ==================== UTILITIES ====================

function showError(message, elementId = 'error-message') {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<i class="fa fa-exclamation-circle"></i><span>' + message + '</span>';
        el.style.display = 'flex';
    }
}

function showToast(type, message) {
    if (typeof message === 'undefined') {
        message = type;
        type = 'success';
    }

    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="fa fa-${type === 'success' ? 'check' : 'times'}"></i>
        </div>
        <div class="toast-content">
            <strong>${type === 'success' ? 'Success!' : 'Error!'}</strong>
            <span>${message}</span>
        </div>
    `;

    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast-notification{position:fixed;top:24px;right:24px;background:#1d1d1f;color:#fff;padding:16px 24px;border-radius:14px;display:flex;gap:16px;z-index:9999;transform:translateX(120%);transition:.4s}
            .toast-notification.active{transform:translateX(0)}
            .toast-icon{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center}
            .toast-icon.success{background:#38ef7d}
            .toast-icon.error{background:#ef473a}
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('active'), 10);
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}
