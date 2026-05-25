/**
 * auth.js - Shared Authentication Utilities
 * =========================================
 * Security:
 * - Tokens are stored in HttpOnly cookies set by the backend
 * - Requests include cookies with same-origin credentials
 * - Redirect to login on 401 responses
 * - API base URL configured for both local and production
 */

const API_BASE = window.location.origin + '/api';

function setToken() {}

function getToken() {
    return null;
}

function removeToken() {
    return null;
}

function isAuthenticated() {
    return true;
}

async function authFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };

    let response = await fetch(url, { ...options, headers, credentials: 'same-origin' });

    if (response.status === 401) {
        const refreshResponse = await fetch(API_BASE + '/refresh', {
            method: 'POST',
            credentials: 'same-origin',
        });

        if (refreshResponse.ok) {
            response = await fetch(url, { ...options, headers, credentials: 'same-origin' });
        } else {
            removeToken();
            window.location.href = '/login';
            return null;
        }
    }

    return response;
}

function redirectToLogin() {
    window.location.href = '/login';
}

function redirectToDashboard() {
    window.location.href = '/dashboard';
}

function redirectToRegister() {
    window.location.href = '/register';
}

function showAlert(elementId, message, type = 'error') {
    const alert = document.getElementById(elementId);
    if (!alert) return;
    alert.textContent = message;
    alert.className = `alert alert-${type} show`;
    setTimeout(() => {
        alert.classList.remove('show');
    }, 8000);
}

function hideAlert(elementId) {
    const alert = document.getElementById(elementId);
    if (alert) {
        alert.classList.remove('show');
    }
}

function createParticles(count = 20) {
    const body = document.body;
    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (Math.random() * 8 + 6) + 's';
        particle.style.animationDelay = (Math.random() * 5) + 's';
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        body.appendChild(particle);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    removeToken();
    createParticles(25);
});
