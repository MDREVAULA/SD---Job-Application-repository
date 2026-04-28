/* ============================= */
/*         SIDEBAR               */
/* ============================= */
document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("toggleBtn");
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

    overlay.addEventListener("click", closeSidebar);

    document.addEventListener("click", function (e) {
        if (
            sidebar.classList.contains("active") &&
            !sidebar.contains(e.target) &&
            !toggleBtn.contains(e.target)
        ) {
            closeSidebar();
        }
    });

    // Stop all clicks inside the sidebar from bubbling to the document
    sidebar.addEventListener("click", function (e) {
        e.stopPropagation();
    });
});

/* ============================= */
/* DROPDOWN MENU                 */
/* ============================= */
document.addEventListener("DOMContentLoaded", function () {
    const dropdownToggles = document.querySelectorAll(".dropdown-toggle");
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
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

/* ============================================================
   THEME SYSTEM
   ─────────────────────────────────────────────────────────────
   NOTE: The initial theme application (preventing flash) is now
   handled by an inline <script> in <head> of layout.html.
   This file only handles:
     - Syncing UI controls (Settings buttons, sidebar buttons)
     - The applyUserTheme() and guestSetTheme() helpers called
       from settings.js and the sidebar toggle buttons
   ============================================================ */

// ── DOMContentLoaded: sync UI controls ──
document.addEventListener('DOMContentLoaded', function () {
    // Read the already-applied theme from <html data-theme>
    // (set by the inline head script, so it's always correct here)
    const appliedTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const userTheme    = document.body.getAttribute('data-user-theme');
    const isLoggedIn   = !!userTheme;

    if (isLoggedIn) {
        _syncSettingsThemeBtns(appliedTheme);
    } else {
        _syncGuestSidebarBtns(appliedTheme);
    }
});

/**
 * Called by the Settings page Appearance buttons (setTheme in settings.js).
 * Applies the theme visually AND saves it to the DB for logged-in users.
 * This function must be global.
 */
function applyUserTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-user-theme', theme);
    const meta = document.querySelector('meta[name="user-theme"]');
    if (meta) meta.content = theme;  // keep meta in sync for the current session
    // Do NOT write localStorage for logged-in users — the server is the source of truth
    _syncSettingsThemeBtns(theme);
}

/**
 * Guest-only: toggle theme via the sidebar buttons.
 * Saves to localStorage only (no DB call).
 */
function guestSetTheme(theme) {
    try { localStorage.setItem('guestTheme', theme); } catch (e) {}
    document.documentElement.setAttribute('data-theme', theme);
    _syncGuestSidebarBtns(theme);
}

// ── Internal helpers ──

// FIX: use data-theme attribute for reliable matching instead of onclick string parsing
function _syncSettingsThemeBtns(theme) {
    document.querySelectorAll('.theme-btn').forEach(btn => {
        const btnTheme = btn.dataset.theme
            || (btn.getAttribute('onclick') || '').match(/setTheme\(['"](\w+)['"]\)/)?.[1];
        btn.classList.toggle('active', btnTheme === theme);
    });
}

function _syncGuestSidebarBtns(theme) {
    const light = document.getElementById('sidebarThemeLight');
    const dark  = document.getElementById('sidebarThemeDark');
    if (light) light.classList.toggle('active', theme === 'light');
    if (dark)  dark.classList.toggle('active',  theme === 'dark');
}

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

    const isHR          = document.body.classList.contains('is-hr');
    const isApplicant   = document.body.classList.contains('is-applicant');
    const API_BASE      = isApplicant ? '/applicant/notifications'
                        : isHR       ? '/hr/notifications'
                        :              '/recruiter/notifications';
    const MARK_READ   = API_BASE + '/mark-read';
    const CSRF        = document.querySelector('meta[name="csrf-token"]')?.content || '';

    let lastUnreadCount = 0;
    let shownToastIds   = new Set();
    let panelOpen       = false;
    // Tracks the current unread count shown in the badge so single-click
    // decrements are applied accurately without waiting for a re-poll.
    let currentUnread   = 0;

    function postJSON(url, body) {
        return fetch(url, {
            method:  'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  CSRF
            },
            body: body ? JSON.stringify(body) : undefined
        });
    }

    notifBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        panelOpen = !panelOpen;
        notifPanel.classList.toggle('open', panelOpen);
        if (panelOpen) loadNotifications(false);
    });

    document.addEventListener('click', function (e) {
        if (panelOpen && !notifWrapper.contains(e.target)) {
            panelOpen = false;
            notifPanel.classList.remove('open');
        }
    });

    notifMarkAll.addEventListener('click', function (e) {
        e.stopPropagation();
        postJSON(MARK_READ)
            .then(() => loadNotifications(false));
    });

    notifClear.addEventListener('click', function (e) {
        e.stopPropagation();
        postJSON(API_BASE + '/clear-all')
            .then(() => {
                notifList.innerHTML = `
                    <div class="notif-empty">
                        <i class="fas fa-bell-slash"></i>
                        <p>No notifications yet</p>
                    </div>`;
                updateBadge(0);
            });
    });

    const TYPE_META = {
        new_application:    { icon: 'fa-file-alt',        title: 'New Application' },
        interview_scheduled:{ icon: 'fa-calendar-check',  title: 'Interview Scheduled' },
        new_message:        { icon: 'fa-comment-dots',    title: 'New Message' },
        new_follow:         { icon: 'fa-user-plus',       title: 'New Follower' },
        job_update:         { icon: 'fa-briefcase',       title: 'Job Update' },
        application_status: { icon: 'fa-clipboard-check', title: 'Application Update' },
    };

    function getTypeMeta(type) {
        return TYPE_META[type] || { icon: 'fa-bell', title: 'Notification' };
    }

    function getNotifUrl(n) {
        if (n.type === 'new_message') {
            return n.sender_id ? '/chat/inbox/' + n.sender_id : '/chat/inbox';
        }
        if (n.type === 'new_follow' || n.type === 'follow_accepted') {
            return n.sender_id ? '/profile/' + n.sender_id : '#';
        }
        if (isApplicant) {
            if (n.type === 'application_status' || n.type === 'interview_scheduled') {
                return '/applicant/status';
            }
            if (n.type === 'job_update' && n.job_id) {
                return '/applicant/job/' + n.job_id;
            }
            if (n.type === 'profile_complete') {
                return '/applicant/status';
            }
            return '#';
        }
        if (n.job_id) return isHR
            ? '/hr/job-applications/' + n.job_id
            : '/recruiter/job-applications/' + n.job_id;
        return '#';
    }

    function loadNotifications(silent) {
        fetch(API_BASE)
            .then(r => { if (!r.ok) return null; return r.json(); })
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
                currentUnread   = count;
                lastUnreadCount = count;

                if (!silent || panelOpen) renderList(data.notifications);
            })
            .catch(() => {});
    }

    function updateBadge(count) {
        if (count > 0) {
            notifBadge.textContent = count > 99 ? '99+' : count;
            notifBadge.style.display = 'inline-flex';
            notifBtn.classList.add('has-unread');
        } else {
            notifBadge.style.display = 'none';
            notifBtn.classList.remove('has-unread');
        }
    }

    /**
     * Mark a single notification as read, decrement the badge by 1,
     * then navigate to the destination URL.
     */
    function markAndRedirect(notifId, el, url) {
        const wasUnread = el.classList.contains('unread');

        // Optimistically update UI
        if (wasUnread) {
            el.classList.remove('unread');
            currentUnread = Math.max(0, currentUnread - 1);
            updateBadge(currentUnread);
        }

        if (!wasUnread) {
            // Already read — navigate immediately, no API call needed
            if (url && url !== '#') window.location.href = url;
            return;
        }

        // Persist to DB then navigate
        postJSON(MARK_READ, { id: notifId })
            .catch(() => {})
            .finally(() => {
                if (url && url !== '#') window.location.href = url;
            });
    }

    function attachNotifClicks() {
        notifList.querySelectorAll('.notif-item[data-id]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                e.stopPropagation();
                markAndRedirect(
                    parseInt(this.dataset.id),
                    this,
                    this.dataset.url
                );
            });
        });
    }

    function renderList(notifications) {
        if (!notifications || notifications.length === 0) {
            notifList.innerHTML = `<div class="notif-empty"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>`;
            return;
        }
        // Use data-id and data-url instead of inline onclick so markAndRedirect can fire
        notifList.innerHTML = notifications.map(function (n) {
            const meta = getTypeMeta(n.type);
            const url  = getNotifUrl(n);
            return `
            <div class="notif-item ${n.is_read ? '' : 'unread'}"
                 data-id="${n.id}"
                 data-url="${url}"
                 style="cursor:pointer;">
                <div class="notif-icon type-${n.type}" style="pointer-events:none;">
                    <i class="fas ${meta.icon}"></i>
                </div>
                <div class="notif-body" style="pointer-events:none;">
                    <p class="notif-msg">${n.message}</p>
                    <span class="notif-time"><i class="fas fa-clock"></i> ${n.created_at}</span>
                </div>
            </div>`;
        }).join('');

        // Wire up click handlers AFTER innerHTML is set
        attachNotifClicks();
    }

    function showToast(notif) {
        if (document.querySelectorAll('.notif-toast').length >= 3) return;
        const meta  = getTypeMeta(notif.type);
        const toast = document.createElement('div');
        toast.className = `notif-toast type-${notif.type}`;
        toast.innerHTML = `
            <div class="notif-toast-icon"><i class="fas ${meta.icon}"></i></div>
            <div class="notif-toast-body">
                <div class="notif-toast-title">${meta.title}</div>
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
        setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }

    lastUnreadCount = -1;
    loadNotifications(true);
    lastUnreadCount = 0;
    setInterval(function () { loadNotifications(true); }, 15000);

});