/**
 * Employee List Toggle Functionality
 * Switches between Employees and Pending Onboarding views
 */

(function() {
    'use strict';

    function initEmployeeToggle() {
        const wrapper = document.querySelector('.emp-wrapper');
        if (!wrapper) return;

        const pendingCard = wrapper.querySelector('.emp-card[style*="margin-bottom"]');
        const employeesCard = wrapper.querySelector('.emp-card:not([style*="margin-bottom"])');

        if (!pendingCard && !employeesCard) return;

        const toggleBar = document.createElement('div');
        toggleBar.className = 'emp-toggle-bar';
        toggleBar.innerHTML = `
            <button class="emp-toggle-btn active" data-view="employees">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                Employees
            </button>
            <button class="emp-toggle-btn" data-view="pending">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                </svg>
                Pending Onboarding
                ${getPendingCount()}
            </button>
        `;

        const statsRow = wrapper.querySelector('.emp-stats-row');
        if (statsRow && statsRow.nextElementSibling) {
            wrapper.insertBefore(toggleBar, statsRow.nextElementSibling);
        } else {
            wrapper.insertBefore(toggleBar, wrapper.firstElementChild);
        }

        if (pendingCard) {
            pendingCard.setAttribute('data-toggle-view', 'pending');
            pendingCard.style.display = 'none';
        }

        if (employeesCard) {
            employeesCard.setAttribute('data-toggle-view', 'employees');
            employeesCard.style.display = 'block';
        }

        const toggleButtons = toggleBar.querySelectorAll('.emp-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const targetView = this.getAttribute('data-view');

                toggleButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                if (pendingCard) {
                    pendingCard.style.display = targetView === 'pending' ? 'block' : 'none';
                }

                if (employeesCard) {
                    employeesCard.style.display = targetView === 'employees' ? 'block' : 'none';
                }
            });
        });
    }

    function getPendingCount() {
        const notifDot = document.querySelector('.emp-notif-dot');
        if (notifDot) {
            return `<span class="emp-toggle-badge">${notifDot.textContent}</span>`;
        }
        return '';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEmployeeToggle);
    } else {
        initEmployeeToggle();
    }
})();