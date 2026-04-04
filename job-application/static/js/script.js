document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("toggleBtn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    function openSidebar() {
        sidebar.classList.add("active");
        overlay.classList.add("active");
    }

    function closeSidebar() {
        sidebar.classList.remove("active");
        overlay.classList.remove("active");
    }

    toggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        if (sidebar.classList.contains("active")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    overlay.addEventListener("click", closeSidebar);
});

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleBtn');
    const closeBtn = document.getElementById('closeBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    // BUKAS: Gamit ang hamburger
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    });

    // SARA: Gamit ang X sa tabi ng Logo
    closeBtn.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });

    // SARA: Gamit ang overlay
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });
});


/* ============================= */
/* DROPDOWN MENU (RECRUITER) */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {

    const dropdownToggles = document.querySelectorAll(".dropdown-toggle");

    dropdownToggles.forEach(toggle => {

        toggle.addEventListener("click", function(e){

            e.preventDefault();

            const submenu = this.nextElementSibling;

            submenu.classList.toggle("open");

        });

    });

});

/* ============================= */
/*         FLASH MESSAGE         */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {

    const flashes = document.querySelectorAll(".flash");

    if (flashes.length > 0) {

        setTimeout(function () {

            flashes.forEach(function (flash) {

                flash.style.transition = "opacity 0.5s ease";
                flash.style.opacity = "0";

                setTimeout(function () {
                    flash.remove();
                }, 500);

            });

        }, 2000); // 4 seconds

    }

});

/* ============================= */
/*        THEME TOGGLE           */
/* ============================= */

(function () {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
})();

document.addEventListener('DOMContentLoaded', function () {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (theme === 'light') {
            themeIcon.className = 'fas fa-sun';
        } else {
            themeIcon.className = 'fas fa-moon';
        }
    }

    // Apply icon on load
    const currentTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(currentTheme);

    themeToggleBtn.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
});

/* ============================= */
/*   RECRUITER NOTIFICATIONS     */
/* ============================= */
document.addEventListener('DOMContentLoaded', function () {
    // Hard exit for non-recruiters — must be outside the IIFE
    if (!document.getElementById('notifWrapper')) return;

(function () {
    const notifWrapper = document.getElementById('notifWrapper');

    const notifBtn       = document.getElementById('notifBtn');
    const notifPanel     = document.getElementById('notifPanel');
    const notifBadge     = document.getElementById('notifBadge');
    const notifList      = document.getElementById('notifList');
    const notifMarkAll   = document.getElementById('notifMarkAllBtn');
    const notifClear     = document.getElementById('notifClearBtn');

    let lastUnreadCount  = 0;
    let shownToastIds    = new Set();
    let panelOpen        = false;

    // ── Toggle panel ──
    notifBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        panelOpen = !panelOpen;
        notifPanel.classList.toggle('open', panelOpen);
        if (panelOpen) {
            loadNotifications(false);
        }
    });

    // ── Close panel on outside click ──
    document.addEventListener('click', function (e) {
        if (panelOpen && !notifWrapper.contains(e.target)) {
            panelOpen = false;
            notifPanel.classList.remove('open');
        }
    });

    // ── Mark all as read ──
    notifMarkAll.addEventListener('click', function (e) {
        e.stopPropagation();
        fetch('/recruiter/notifications/mark-read', { method: 'POST' })
            .then(() => loadNotifications(false));
    });

    // ── Clear all ──
    notifClear.addEventListener('click', function (e) {
        e.stopPropagation();
        fetch('/recruiter/notifications/clear-all', { method: 'POST' })
            .then(() => {
                notifList.innerHTML = `
                    <div class="notif-empty">
                        <i class="fas fa-bell-slash"></i>
                        <p>No notifications yet</p>
                    </div>`;
                updateBadge(0);
            });
    });

    // ── Fetch & render notifications ──
    function loadNotifications(silent) {
        fetch('/recruiter/notifications')
            .then(r => {
                if (!r.ok) return null;
                return r.json();
            })
            .then(data => {
                if (!data || data.error) return;
                const count = data.unread_count || 0;

                // Show popup toasts for NEW unread items (only when panel is closed)
                if (!panelOpen) {
                    data.notifications.forEach(function (n) {
                        if (!n.is_read && !shownToastIds.has(n.id)) {
                            shownToastIds.add(n.id);
                            showToast(n);
                        }
                    });
                }

                // Bell ring animation on new notifications
                if (!silent && count > lastUnreadCount && lastUnreadCount !== -1) {
                    notifBtn.classList.remove('has-unread');
                    void notifBtn.offsetWidth; // reflow to restart animation
                    notifBtn.classList.add('has-unread');
                }

                updateBadge(count);
                lastUnreadCount = count;

                if (!silent || panelOpen) {
                    renderList(data.notifications);
                }

                // Mark all read once panel is opened
                if (panelOpen && count > 0) {
                    fetch('/recruiter/notifications/mark-read', { method: 'POST' })
                        .then(() => updateBadge(0));
                }
            })
            .catch(() => {});
    }

    function updateBadge(count) {
        if (count > 0) {
            notifBadge.textContent = count > 99 ? '99+' : count;
            notifBadge.style.display = 'inline-flex';
        } else {
            notifBadge.style.display = 'none';
            notifBtn.classList.remove('has-unread');
        }
    }

    function renderList(notifications) {
        if (!notifications || notifications.length === 0) {
            notifList.innerHTML = `
                <div class="notif-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications yet</p>
                </div>`;
            return;
        }

        notifList.innerHTML = notifications.map(function (n) {
            const icon = n.type === 'interview_scheduled'
                ? '<i class="fas fa-calendar-check"></i>'
                : '<i class="fas fa-file-alt"></i>';
            return `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
                <div class="notif-icon type-${n.type}">${icon}</div>
                <div class="notif-body">
                    <p class="notif-msg">${n.message}</p>
                    <span class="notif-time"><i class="fas fa-clock"></i> ${n.created_at}</span>
                </div>
            </div>`;
        }).join('');
    }

    // ── Toast popup ──
    function showToast(notif) {
        const existing = document.querySelectorAll('.notif-toast');
        // Max 3 toasts at a time
        if (existing.length >= 3) return;

        const icon = notif.type === 'interview_scheduled'
            ? '<i class="fas fa-calendar-check"></i>'
            : '<i class="fas fa-file-alt"></i>';
        const title = notif.type === 'interview_scheduled'
            ? 'Interview Scheduled'
            : 'New Job Application';

        const toast = document.createElement('div');
        toast.className = `notif-toast type-${notif.type}`;
        toast.innerHTML = `
            <div class="notif-toast-icon">${icon}</div>
            <div class="notif-toast-body">
                <div class="notif-toast-title">${title}</div>
                <div class="notif-toast-msg">${notif.message}</div>
            </div>
            <button class="notif-toast-close" title="Dismiss"><i class="fas fa-times"></i></button>`;

        document.body.appendChild(toast);

        // Dismiss on close button
        toast.querySelector('.notif-toast-close').addEventListener('click', function (e) {
            e.stopPropagation();
            dismissToast(toast);
        });

        // Dismiss on click (open panel)
        toast.addEventListener('click', function () {
            dismissToast(toast);
            panelOpen = true;
            notifPanel.classList.add('open');
            loadNotifications(false);
        });

        // Auto-dismiss after 5s
        setTimeout(function () { dismissToast(toast); }, 5000);
    }

    function dismissToast(toast) {
        if (!toast || !toast.parentNode) return;
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(function () {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
    }

    // ── Initial load + polling every 15s ──
    lastUnreadCount = -1; // sentinel so first load doesn't animate
    loadNotifications(true);
    lastUnreadCount = 0;
    setInterval(function () { loadNotifications(true); }, 15000);
})();
}); // end DOMContentLoaded