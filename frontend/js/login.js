// login.js — Login page behavior

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('login-alert');

        const btn = document.getElementById('login-btn');
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!username || !password) {
            showAlert('login-alert', 'Please enter both username and password.', 'error');
            return;
        }

        btn.classList.add('loading');
        btn.disabled = true;

        try {
            const response = await fetch(API_BASE + '/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    username: username,
                    password: password,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('login-alert', 'Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    redirectToDashboard();
                }, 1000);
            } else if (response.status === 429) {
                showAlert('login-alert', 'Too many login attempts. Please wait 1 minute.', 'warning');
            } else if (response.status === 403) {
                showAlert('login-alert', data.detail || 'Account locked. Please try again later.', 'warning');
            } else {
                showAlert('login-alert', data.detail || 'Invalid username or password.', 'error');
            }
        } catch (error) {
            showAlert('login-alert', 'Network error. Please check your connection.', 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    });
});
