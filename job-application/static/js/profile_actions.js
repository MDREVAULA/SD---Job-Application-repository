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

                <!-- ── Evidence Upload ── -->
                <div class="pam-report-field" style="margin-top:14px;">
                    <label class="pam-field-label">
                        Evidence
                        <span>(optional · up to 5 files · jpg, png, gif, mp4, pdf · max 10 MB each)</span>
                    </label>
                    <div class="pam-evidence-drop" id="pamEvidenceDrop" onclick="document.getElementById('pamEvidenceInput').click()">
                        <input type="file" id="pamEvidenceInput" multiple accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.pdf" style="display:none;">
                        <svg viewBox="0 0 24 24" class="pam-evidence-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <span class="pam-evidence-label">Click to upload files</span>
                        <span class="pam-evidence-sub">or drag and drop</span>
                    </div>
                    <div id="pamEvidenceList" class="pam-evidence-list"></div>
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

        <style>
        /* ── Evidence drop zone ── */
        .pam-evidence-drop {
            border: 2px dashed var(--border-color, #e5e7eb);
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.18s, background 0.18s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }
        .pam-evidence-drop:hover,
        .pam-evidence-drop.drag-over {
            border-color: #dc2626;
            background: #fef2f2;
        }
        .pam-evidence-icon {
            width: 28px;
            height: 28px;
            stroke: #9ca3af;
            fill: none;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            margin-bottom: 2px;
        }
        .pam-evidence-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary, #374151);
        }
        .pam-evidence-sub {
            font-size: 0.75rem;
            color: var(--text-muted, #9ca3af);
        }

        /* ── File list ── */
        .pam-evidence-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 8px;
        }
        .pam-evidence-item {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 8px 12px;
            background: var(--bg-surface-alt, #f9fafb);
            border: 1px solid var(--border-color, #e5e7eb);
            border-radius: 8px;
            font-size: 0.82rem;
        }
        .pam-evidence-item-icon {
            font-size: 1rem;
            flex-shrink: 0;
            color: #6b7280;
        }
        .pam-evidence-item-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--text-secondary, #374151);
            font-weight: 500;
        }
        .pam-evidence-item-size {
            font-size: 0.72rem;
            color: var(--text-muted, #9ca3af);
            flex-shrink: 0;
        }
        .pam-evidence-item-remove {
            background: none;
            border: none;
            cursor: pointer;
            color: #9ca3af;
            padding: 2px 4px;
            border-radius: 4px;
            font-size: 0.8rem;
            flex-shrink: 0;
            transition: color 0.12s;
        }
        .pam-evidence-item-remove:hover { color: #dc2626; }

        /* ── Preview thumbnail ── */
        .pam-evidence-thumb {
            width: 32px;
            height: 32px;
            border-radius: 4px;
            object-fit: cover;
            flex-shrink: 0;
        }

        [data-theme="dark"] .pam-evidence-drop { border-color: var(--border-color); }
        [data-theme="dark"] .pam-evidence-drop:hover { background: rgba(220,38,38,0.08); }
        [data-theme="dark"] .pam-evidence-item { background: rgba(255,255,255,0.04); border-color: var(--border-color); }
        [data-theme="dark"] .pam-evidence-item-name { color: var(--text-secondary); }
        </style>
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

    // ── Evidence file handling ───────────────────────────────────
    let evidenceFiles = [];
    const MAX_FILES   = 5;
    const MAX_SIZE    = 10 * 1024 * 1024;
    const ALLOWED_EXT = new Set(['.jpg','.jpeg','.png','.gif','.webp','.mp4','.pdf']);

    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function fileIcon(name) {
        const ext = name.toLowerCase().split('.').pop();
        if (['jpg','jpeg','png','gif','webp'].includes(ext)) return '🖼️';
        if (ext === 'mp4') return '🎥';
        if (ext === 'pdf') return '📄';
        return '📎';
    }

    function renderEvidenceList() {
        const list = $('pamEvidenceList');
        if (!list) return;
        list.innerHTML = '';
        evidenceFiles.forEach((f, i) => {
            const isImage = f.type.startsWith('image/');
            const item = document.createElement('div');
            item.className = 'pam-evidence-item';

            let thumbHtml = '';
            if (isImage) {
                const url = URL.createObjectURL(f);
                thumbHtml = `<img src="${url}" class="pam-evidence-thumb" alt="">`;
            } else {
                thumbHtml = `<span class="pam-evidence-item-icon">${fileIcon(f.name)}</span>`;
            }

            item.innerHTML = `
                ${thumbHtml}
                <span class="pam-evidence-item-name" title="${f.name}">${f.name}</span>
                <span class="pam-evidence-item-size">${formatBytes(f.size)}</span>
                <button class="pam-evidence-item-remove" title="Remove" data-index="${i}">✕</button>
            `;
            list.appendChild(item);
        });

        list.querySelectorAll('.pam-evidence-item-remove').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                const idx = parseInt(this.dataset.index);
                evidenceFiles.splice(idx, 1);
                renderEvidenceList();
            });
        });
    }

    function addFiles(newFiles) {
        const errEl = $('pamReportError');
        for (const f of newFiles) {
            if (evidenceFiles.length >= MAX_FILES) {
                if (errEl) { errEl.textContent = `Maximum ${MAX_FILES} files allowed.`; errEl.style.display = 'flex'; }
                break;
            }
            const ext = '.' + f.name.toLowerCase().split('.').pop();
            if (!ALLOWED_EXT.has(ext)) {
                toast(`${f.name}: unsupported file type`, 'error');
                continue;
            }
            if (f.size > MAX_SIZE) {
                toast(`${f.name}: exceeds 10 MB limit`, 'error');
                continue;
            }
            evidenceFiles.push(f);
        }
        renderEvidenceList();
    }

    // Wire up file input
    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'pamEvidenceInput') {
            addFiles(Array.from(e.target.files));
            e.target.value = ''; // reset so same file can be re-added after removal
        }
    });

    // Drag and drop
    document.addEventListener('dragover', function (e) {
        const drop = $('pamEvidenceDrop');
        if (drop && drop.contains(e.target)) {
            e.preventDefault();
            drop.classList.add('drag-over');
        }
    });

    document.addEventListener('dragleave', function (e) {
        const drop = $('pamEvidenceDrop');
        if (drop && !drop.contains(e.relatedTarget)) {
            drop.classList.remove('drag-over');
        }
    });

    document.addEventListener('drop', function (e) {
        const drop = $('pamEvidenceDrop');
        if (drop && drop.contains(e.target)) {
            e.preventDefault();
            drop.classList.remove('drag-over');
            addFiles(Array.from(e.dataTransfer.files));
        }
    });

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
        evidenceFiles = [];
        renderEvidenceList();
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

    // ── submit report (uses FormData for file upload) ─────────────
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

        // Build FormData so we can attach files
        const formData = new FormData();
        formData.append('reason', reason);
        formData.append('description', desc);
        evidenceFiles.forEach(f => formData.append('evidence', f));

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        fetch(`/user/report/${uid}`, {
            method : 'POST',
            headers: { 
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            body   : formData,
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