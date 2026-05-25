/**
 * password-strength.js — Real-time Password Strength Meter
 * =========================================================
 * Security:
 * - Client-side validation for UX (real-time feedback)
 * - Server-side validation is the authoritative check
 * - Rules match server-side requirements exactly
 *
 * Rules:
 * - Minimum 12 characters
 * - At least 1 uppercase letter
 * - At least 1 lowercase letter
 * - At least 1 digit
 * - At least 1 special character
 */

/**
 * Evaluate password strength and return detailed results.
 * @param {string} password - The password to evaluate
 * @returns {Object} - { strength, checks, passed, total }
 */
function evaluatePasswordStrength(password) {
    const checks = {
        minLength: password.length >= 12,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        digit: /\d/.test(password),
        special: /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?\/~`\\]/.test(password),
    };

    const passed = Object.values(checks).filter(Boolean).length;
    const total = Object.keys(checks).length;

    let strength = 'none';
    if (password.length === 0) {
        strength = 'none';
    } else if (passed <= 2) {
        strength = 'weak';
    } else if (passed <= 4) {
        strength = 'medium';
    } else {
        strength = 'strong';
    }

    return { strength, checks, passed, total };
}

/**
 * Update the password strength UI elements.
 * Called on every keystroke in the password field.
 * @param {string} password - Current password value
 */
function updateStrengthMeter(password) {
    const result = evaluatePasswordStrength(password);

    // Update strength bar
    const fill = document.getElementById('strength-bar-fill');
    const label = document.getElementById('strength-label');

    if (fill) {
        fill.className = 'strength-bar-fill';
        if (result.strength !== 'none') {
            fill.classList.add(result.strength);
        }
    }

    if (label) {
        if (result.strength === 'none') {
            label.textContent = '';
            label.className = 'strength-label';
        } else {
            label.textContent = result.strength.charAt(0).toUpperCase() + result.strength.slice(1);
            label.className = `strength-label ${result.strength}`;
        }
    }

    // Update individual rule indicators
    const ruleMap = {
        'rule-length': result.checks.minLength,
        'rule-uppercase': result.checks.uppercase,
        'rule-lowercase': result.checks.lowercase,
        'rule-digit': result.checks.digit,
        'rule-special': result.checks.special,
    };

    for (const [id, passed] of Object.entries(ruleMap)) {
        const el = document.getElementById(id);
        if (el) {
            if (passed) {
                el.classList.add('passed');
            } else {
                el.classList.remove('passed');
            }
            // Update the icon
            const icon = el.querySelector('.rule-icon');
            if (icon) {
                icon.textContent = passed ? '✓' : '';
            }
        }
    }

    return result;
}

/**
 * Initialize the password strength meter on a given input field.
 * @param {string} inputId - ID of the password input element
 */
function initPasswordStrengthMeter(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('input', function () {
        updateStrengthMeter(this.value);
    });
}
