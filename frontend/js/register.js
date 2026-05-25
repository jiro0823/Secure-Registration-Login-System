// register.js — Registration page behavior

document.addEventListener('DOMContentLoaded', () => {
    initPasswordStrengthMeter('password');

    const form = document.getElementById('register-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('register-alert');

        const btn = document.getElementById('register-btn');
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (!username || !password || !confirmPassword) {
            showAlert('register-alert', 'All fields are required.', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showAlert('register-alert', 'Passwords do not match.', 'error');
            return;
        }

        const strength = evaluatePasswordStrength(password);
        if (strength.strength !== 'strong') {
            showAlert('register-alert', 'Please create a stronger password meeting all requirements.', 'warning');
            return;
        }

        btn.classList.add('loading');
        btn.disabled = true;

        try {
            const response = await fetch(API_BASE + '/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    username: username,
                    password: password,
                    confirm_password: confirmPassword,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('register-alert', 'Registration successful! Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                showAlert('register-alert', data.detail || 'Registration failed. Please try again.', 'error');
            }
        } catch (error) {
            showAlert('register-alert', 'Network error. Please check your connection.', 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    });
});
