/* ============================= */
/*         SIDEBAR               */
/* ============================= */
document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("toggleBtn");
    const closeBtn  = document.getElementById("closeBtn");
    const sidebar   = document.getElementById("sidebar");
    const overlay   = document.getElementById("sidebar-overlay");

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
        sidebar.classList.contains("active") ? closeSidebar() : openSidebar();
    });
    closeBtn.addEventListener("click", closeSidebar);
    overlay.addEventListener("click", closeSidebar);
});

/* ============================= */
/* DROPDOWN MENU                 */
/* ============================= */
document.addEventListener("DOMContentLoaded", function () {
    const dropdownToggles = document.querySelectorAll(".dropdown-toggle");
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener("click", function (e) {
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
                setTimeout(function () { flash.remove(); }, 500);
            });
        }, 2000);
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
    const themeIcon      = document.getElementById('themeIcon');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        themeIcon.className = theme === 'light' ? 'fas fa-sun' : 'fas fa-moon';
    }

    applyTheme(localStorage.getItem('theme') || 'dark');

    themeToggleBtn.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
});

/* =============================== */
/* RECRUITER / HR NOTIFICATIONS    */
/* =============================== */
document.addEventListener('DOMContentLoaded', function () {

    const notifWrapper = document.getElementById('notifWrapper');
    if (!notifWrapper) return;

    const notifBtn     = document.getElementById('notifBtn');
    const notifPanel   = document.getElementById('notifPanel');
    const notifBadge   = document.getElementById('notifBadge');
    const notifList    = document.getElementById('notifList');
    const notifMarkAll = document.getElementById('notifMarkAllBtn');
    const notifClear   = document.getElementById('notifClearBtn');

    const isHR       = document.body.classList.contains('is-hr');
    const API_BASE   = isHR ? '/hr/notifications' : '/recruiter/notifications';

    let lastUnreadCount = 0;
    let shownToastIds   = new Set();
    let panelOpen       = false;

    // ── Toggle panel ──
    notifBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        panelOpen = !panelOpen;
        notifPanel.classList.toggle('open', panelOpen);
        if (panelOpen) loadNotifications(false);
    });

    // ── Close on outside click ──
    document.addEventListener('click', function (e) {
        if (panelOpen && !notifWrapper.contains(e.target)) {
            panelOpen = false;
            notifPanel.classList.remove('open');
        }
    });

    // ── Mark all as read ──
    notifMarkAll.addEventListener('click', function (e) {
        e.stopPropagation();
        fetch(API_BASE + '/mark-read', { method: 'POST' })
            .then(() => loadNotifications(false));
    });

    // ── Clear all ──
    notifClear.addEventListener('click', function (e) {
        e.stopPropagation();
        fetch(API_BASE + '/clear-all', { method: 'POST' })
            .then(() => {
                notifList.innerHTML = `
                    <div class="notif-empty">
                        <i class="fas fa-bell-slash"></i>
                        <p>No notifications yet</p>
                    </div>`;
                updateBadge(0);
            });
    });

    // ── Fetch & render ──
    function loadNotifications(silent) {
        fetch(API_BASE)
            .then(r => {
                if (!r.ok) return null;
                return r.json();
            })
            .then(data => {
                if (!data || data.error) return;
                const count = data.unread_count || 0;

                if (!panelOpen) {
                    data.notifications.forEach(function (n) {
                        if (!n.is_read && !shownToastIds.has(n.id)) {
                            shownToastIds.add(n.id);
                            showToast(n);
                        }
                    });
                }

                if (!silent && count > lastUnreadCount && lastUnreadCount !== -1) {
                    notifBtn.classList.remove('has-unread');
                    void notifBtn.offsetWidth;
                    notifBtn.classList.add('has-unread');
                }

                updateBadge(count);
                lastUnreadCount = count;

                if (!silent || panelOpen) renderList(data.notifications);

                if (panelOpen && count > 0) {
                    fetch(API_BASE + '/mark-read', { method: 'POST' })
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
            const url = n.job_id
                ? (isHR ? '/hr/job-applications/' + n.job_id : '/recruiter/job-applications/' + n.job_id)
                : '#';
            return `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}" onclick="window.location.href='${url}'">
                <div class="notif-icon type-${n.type}">${icon}</div>
                <div class="notif-body">
                    <p class="notif-msg">${n.message}</p>
                    <span class="notif-time"><i class="fas fa-clock"></i> ${n.created_at}</span>
                </div>
            </div>`;
        }).join('');
    }

    function showToast(notif) {
        if (document.querySelectorAll('.notif-toast').length >= 3) return;
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
        toast.querySelector('.notif-toast-close').addEventListener('click', function (e) {
            e.stopPropagation();
            dismissToast(toast);
        });
        toast.addEventListener('click', function () {
            dismissToast(toast);
            panelOpen = true;
            notifPanel.classList.add('open');
            loadNotifications(false);
        });
        setTimeout(function () { dismissToast(toast); }, 5000);
    }

    function dismissToast(toast) {
        if (!toast || !toast.parentNode) return;
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(function () {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
    }

    lastUnreadCount = -1;
    loadNotifications(true);
    lastUnreadCount = 0;
    setInterval(function () { loadNotifications(true); }, 15000);

});

document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons = document.querySelectorAll(".delete-hr");

    deleteButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            const hrId = this.dataset.id;
            const hrName = this.dataset.name;

            document.getElementById("confirmMessage").innerHTML =
                `Are you sure you want to delete <strong>${hrName}</strong>? This cannot be undone.`;

            document.getElementById("deleteForm").action =
                `/recruiter/delete-hr/${hrId}`;

            document.getElementById("confirmModal").style.display = "flex";
        });
    });

});

function closeConfirmModal() {
    document.getElementById("confirmModal").style.display = "none";
}
document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons = document.querySelectorAll(".delete-hr");
    const deleteAllBtn = document.getElementById("deleteAllHrBtn");

    deleteButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            const hrId = this.dataset.id;
            const hrName = this.dataset.name;

            document.getElementById("confirmTitle").textContent = "Delete HR Account";
            document.getElementById("confirmMessage").innerHTML =
                `Are you sure you want to delete <strong>${hrName}</strong>? This cannot be undone.`;

            document.getElementById("deleteForm").action =
                `/recruiter/delete-hr/${hrId}`;

            document.getElementById("confirmModal").style.display = "flex";
        });
    });

    if (deleteAllBtn) {
        deleteAllBtn.addEventListener("click", function () {
            document.getElementById("confirmTitle").textContent = "Delete All HR Accounts";
            document.getElementById("confirmMessage").innerHTML =
                `Are you sure you want to delete <strong>all HR accounts</strong>? This cannot be undone.`;

            document.getElementById("deleteForm").action =
                `/recruiter/delete-all-hr`;

            document.getElementById("confirmModal").style.display = "flex";
        });
    }

    const closeButtons = document.querySelectorAll("#confirmModal .hra-modal-close");
    closeButtons.forEach(btn => {
        btn.addEventListener("click", closeConfirmModal);
    });

});

function closeConfirmModal() {
    document.getElementById("confirmModal").style.display = "none";
}
document.addEventListener("DOMContentLoaded", function () {
    const snackbar = document.getElementById("undoSnackbar");

    if (snackbar) {
        setTimeout(() => {
            snackbar.style.opacity = "0";
            snackbar.style.transition = "0.5s ease";
            setTimeout(() => snackbar.remove(), 400);
        }, 5000);
    }
});