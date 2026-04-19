// ================================================================
// static/js/profile_actions.js
// Injects menu, modal, backdrop, toast directly into <body>
// so no parent overflow:hidden can ever clip them.
// Requires: window.PROFILE_USER_ID set before this script loads.
// ================================================================

(function () {
    'use strict';

    let menuOpen   = false;
    let reportOpen = false;
    let isBlocked  = false;

    // ── inject HTML into body ────────────────────────────────────
    function inject() {
        const div = document.createElement('div');
        div.id = 'pamPortal';
        div.innerHTML = `
        <!-- Dropdown menu -->
        <div id="pamMenu" class="pam-menu" role="menu">
            <button class="pam-item pam-item--share" onclick="pamShare()">
                <svg viewBox="0 0 24 24"><path d="M18 16a3 3 0 0 0-2.05.82L8.91 12.7A3.1 3.1 0 0 0 9 12a3.1 3.1 0 0 0-.09-.7l7-4.08A3 3 0 1 0 15 6a3.1 3.1 0 0 0 .09.7l-7 4.08A3 3 0 1 0 6 15a3 3 0 0 0 2.05-.82l7.08 4.15A3 3 0 1 0 18 16Z"/></svg>
                Share Profile
            </button>
            <div class="pam-divider"></div>
            <button class="pam-item pam-item--block" id="pamBlockBtn" onclick="pamBlock()">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                <span id="pamBlockLabel">Block User</span>
            </button>
            <button class="pam-item pam-item--report" onclick="pamOpenReport()">
                <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Report User
            </button>
            <div class="pam-divider"></div>
            <button class="pam-item pam-item--cancel" onclick="pamCloseMenu()">
                <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                Cancel
            </button>
        </div>

        <!-- Backdrop -->
        <div id="pamBackdrop" class="pam-backdrop" onclick="pamCloseReport()"></div>

        <!-- Report modal -->
        <div class="pam-report-modal" id="pamReportModal" role="dialog" aria-modal="true">
            <div class="pam-report-header">
                <h3>
                    <svg class="pam-report-icon" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    Report User
                </h3>
                <button class="pam-report-close" onclick="pamCloseReport()">
                    <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div class="pam-report-body">
                <p class="pam-report-desc">Help us understand what's wrong. Your report is anonymous.</p>
                <p class="pam-reason-label">Select a reason</p>
                <div class="pam-reason-grid">
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Spam"> Spam</label>
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Harassment"> Harassment</label>
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Fake Profile"> Fake Profile</label>
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Scam / Fraud"> Scam / Fraud</label>
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Inappropriate Content"> Inappropriate</label>
                    <label class="pam-reason-chip"><input type="radio" name="pamReason" value="Other"> Other</label>
                </div>
                <div class="pam-report-field">
                    <label class="pam-field-label" for="pamReportDesc">Additional details <span>(optional)</span></label>
                    <textarea id="pamReportDesc" class="pam-field-textarea" placeholder="Describe the issue in more detail..." rows="3"></textarea>
                </div>
                <div id="pamReportError" class="pam-report-error" style="display:none;"></div>
            </div>
            <div class="pam-report-footer">
                <button class="pam-footer-btn pam-footer-btn--cancel" onclick="pamCloseReport()">Cancel</button>
                <button class="pam-footer-btn pam-footer-btn--submit" id="pamSubmitBtn" onclick="pamSubmitReport()">
                    <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>
                    Submit Report
                </button>
            </div>
        </div>

        <!-- Toast -->
        <div class="pam-toast" id="pamToast"></div>
        `;
        document.body.appendChild(div);
    }

    inject();

    // ── helpers ──────────────────────────────────────────────────
    const $ = id => document.getElementById(id);

    function toast(msg, type = 'success') {
        const t = $('pamToast');
        if (!t) return;
        t.textContent = msg;
        t.className   = `pam-toast pam-toast--${type} pam-toast--show`;
        clearTimeout(t._timer);
        t._timer = setTimeout(() => t.classList.remove('pam-toast--show'), 3200);
    }

    // ── position menu under the trigger button ───────────────────
    function positionMenu() {
        const trigger = $('pamTrigger');
        const menu    = $('pamMenu');
        if (!trigger || !menu) return;
        const rect = trigger.getBoundingClientRect();
        // Use fixed so scroll/overflow on any ancestor can never clip it
        menu.style.position = 'fixed';
        menu.style.top      = (rect.bottom + 8) + 'px';
        menu.style.right    = (window.innerWidth - rect.right) + 'px';
        menu.style.left     = 'auto';
    }

    // ── open / close menu ────────────────────────────────────────
    window.pamToggle = function () {
        menuOpen = !menuOpen;
        const menu    = $('pamMenu');
        const trigger = $('pamTrigger');
        if (!menu) return;
        if (menuOpen) {
            positionMenu();
            menu.classList.add('pam-menu--open');
            if (trigger) trigger.classList.add('pam-trigger--open');
        } else {
            pamCloseMenu();
        }
    };

    window.pamCloseMenu = function () {
        menuOpen = false;
        const menu    = $('pamMenu');
        const trigger = $('pamTrigger');
        if (menu)    menu.classList.remove('pam-menu--open');
        if (trigger) trigger.classList.remove('pam-trigger--open');
    };

    // reposition on scroll / resize
    window.addEventListener('scroll', () => { if (menuOpen) positionMenu(); }, { passive: true });
    window.addEventListener('resize', () => { if (menuOpen) positionMenu(); });

    // ── share ────────────────────────────────────────────────────
    window.pamShare = function () {
        pamCloseMenu();
        const url = window.location.href;
        if (navigator.share) {
            navigator.share({ title: document.title, url }).catch(() => {});
        } else if (navigator.clipboard) {
            navigator.clipboard.writeText(url)
                .then(() => toast('Profile link copied!', 'success'))
                .catch(()  => toast('Could not copy link.', 'error'));
        } else {
            toast('Copy: ' + url, 'info');
        }
    };

    // ── block ────────────────────────────────────────────────────
    window.pamBlock = function () {
        pamCloseMenu();
        const uid = window.PROFILE_USER_ID;
        if (!uid) return;
        fetch(`/user/block/${uid}`, {
            method : 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) { toast(data.error, 'error'); return; }
            isBlocked = data.action === 'blocked';
            const lbl = $('pamBlockLabel');
            if (lbl) lbl.textContent = isBlocked ? 'Unblock User' : 'Block User';
            toast(data.message, isBlocked ? 'warning' : 'success');
        })
        .catch(() => toast('Something went wrong.', 'error'));
    };

    // ── open report modal ────────────────────────────────────────
    window.pamOpenReport = function () {
        pamCloseMenu();
        reportOpen = true;
        const bd = $('pamBackdrop');
        const md = $('pamReportModal');
        if (bd) bd.classList.add('pam-backdrop--show');
        if (md) {
            md.style.display = 'flex';
            requestAnimationFrame(() => md.classList.add('pam-report-modal--open'));
        }
        document.body.style.overflow = 'hidden';
        // reset
        document.querySelectorAll('input[name="pamReason"]').forEach(r => r.checked = false);
        const desc = $('pamReportDesc');
        if (desc) desc.value = '';
        const err = $('pamReportError');
        if (err) { err.style.display = 'none'; err.textContent = ''; }
    };

    // ── close report modal ───────────────────────────────────────
    window.pamCloseReport = function () {
        reportOpen = false;
        const bd = $('pamBackdrop');
        const md = $('pamReportModal');
        if (bd) bd.classList.remove('pam-backdrop--show');
        if (md) {
            md.classList.remove('pam-report-modal--open');
            setTimeout(() => { md.style.display = 'none'; }, 220);
        }
        document.body.style.overflow = '';
    };

    // ── submit report ────────────────────────────────────────────
    window.pamSubmitReport = function () {
        const uid      = window.PROFILE_USER_ID;
        const reasonEl = document.querySelector('input[name="pamReason"]:checked');
        const reason   = reasonEl ? reasonEl.value : '';
        const desc     = ($('pamReportDesc') || {}).value || '';
        const errEl    = $('pamReportError');

        if (!reason) {
            if (errEl) { errEl.textContent = 'Please select a reason.'; errEl.style.display = 'flex'; }
            return;
        }
        if (errEl) errEl.style.display = 'none';

        const btn = $('pamSubmitBtn');
        if (btn) { btn.disabled = true; btn.textContent = 'Submitting…'; }

        fetch(`/user/report/${uid}`, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            body   : JSON.stringify({ reason, description: desc }),
        })
        .then(r => r.json())
        .then(data => {
            if (btn) {
                btn.disabled  = false;
                btn.innerHTML = '<svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg> Submit Report';
            }
            if (data.error) {
                if (errEl) { errEl.textContent = data.error; errEl.style.display = 'flex'; }
                return;
            }
            pamCloseReport();
            toast(data.message || 'Report submitted.', 'success');
        })
        .catch(() => {
            if (btn) { btn.disabled = false; btn.textContent = 'Submit Report'; }
            toast('Something went wrong.', 'error');
        });
    };

    // ── outside click closes menu ────────────────────────────────
    document.addEventListener('click', function (e) {
        const trigger = $('pamTrigger');
        const menu    = $('pamMenu');
        if (menuOpen && trigger && menu &&
            !trigger.contains(e.target) && !menu.contains(e.target)) {
            pamCloseMenu();
        }
    });

    // ── escape key ───────────────────────────────────────────────
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (reportOpen) pamCloseReport();
            else if (menuOpen) pamCloseMenu();
        }
    });

    // ── init block status ────────────────────────────────────────
    (function () {
        const uid = window.PROFILE_USER_ID;
        if (!uid) return;
        fetch(`/user/block-status/${uid}`)
            .then(r => r.json())
            .then(data => {
                isBlocked = data.is_blocked;
                const lbl = $('pamBlockLabel');
                if (lbl) lbl.textContent = isBlocked ? 'Unblock User' : 'Block User';
            })
            .catch(() => {});
    })();

})();