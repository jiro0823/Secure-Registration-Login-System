// dashboard.js — Dashboard page behavior

document.addEventListener('DOMContentLoaded', async () => {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await fetch(API_BASE + '/logout', {
                method: 'POST',
                credentials: 'same-origin',
            });
            removeToken();
            window.location.href = '/login';
        });
    }

    try {
        const response = await authFetch(API_BASE + '/me');
        if (!response) return;

        if (response.ok) {
            const user = await response.json();
            document.getElementById('display-username').textContent = user.username;
            document.getElementById('display-id').textContent = '#' + user.id;
            document.getElementById('display-user').textContent = user.username;
            document.getElementById('display-created').textContent = new Date(user.created_at).toLocaleString();
        } else {
            removeToken();
            redirectToLogin();
        }
    } catch (error) {
        removeToken();
        redirectToLogin();
    }
});
