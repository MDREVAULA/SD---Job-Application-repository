/* ============================================================
   HR PROFILE JS — Complete (merged with recruiter features)
   Includes: Portfolio upload, file validation, custom modals,
   education delete confirmation, checkbox handling, etc.
   ============================================================ */

/* ────────────────────────────────────────────────────────────
   TOGGLE HELPERS
   ──────────────────────────────────────────────────────────── */

function toggleEdit(section) {
    const view = document.getElementById('view-' + section);
    const form = document.getElementById('edit-' + section);
    if (!view || !form) return;

    const isEditing = form.dataset.open === 'true';

    if (isEditing) {
        form.dataset.open = 'false';
        form.style.display = 'none';
        view.style.display = '';
    } else {
        form.dataset.open = 'true';
        form.style.display = '';
        view.style.display = 'none';
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    document.querySelectorAll('[data-edit-target="' + section + '"]').forEach(btn => {
        btn.innerHTML = isEditing
            ? '<i class="fas fa-pen"></i> Edit'
            : '<i class="fas fa-times"></i> Cancel';
    });
}

function toggleAddForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const isVisible = form.dataset.open === 'true';

    if (isVisible) {
        form.dataset.open = 'false';
        form.style.display = 'none';
    } else {
        form.dataset.open = 'true';
        form.style.display = '';
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function toggleEndDate(endDateId, checkbox) {
    const endDate = document.getElementById(endDateId);
    if (!endDate) return;
    endDate.disabled = checkbox.checked;
    if (checkbox.checked) endDate.value = '';
}

/* ────────────────────────────────────────────────────────────
   CUSTOM CHECKBOXES
   ──────────────────────────────────────────────────────────── */

function initCustomCheckboxes() {
    document.querySelectorAll('.prof-checkbox-label').forEach(label => {
        const input = label.querySelector('input[type="checkbox"]');
        if (!input) return;

        if (input.checked) label.classList.add('is-checked');

        label.addEventListener('click', function () {
            setTimeout(() => {
                if (input.checked) {
                    label.classList.add('is-checked');
                } else {
                    label.classList.remove('is-checked');
                }

                const formGrid = label.closest('.prof-form-grid');
                if (formGrid) {
                    const endDateInput = formGrid.querySelector('input[type="month"][name="end_date"]');
                    if (endDateInput) {
                        endDateInput.disabled = input.checked;
                        if (input.checked) endDateInput.value = '';
                    }
                }
            }, 0);
        });
    });
}

/* ────────────────────────────────────────────────────────────
   CUSTOM CONFIRM MODAL
   ──────────────────────────────────────────────────────────── */

function showConfirmModal({ title, message, confirmLabel = 'Delete', confirmClass = 'danger', confirmIcon = 'fa-trash', onConfirm }) {
    const existing = document.getElementById('prof-confirm-modal-wrap');
    if (existing) existing.remove();

    const wrap = document.createElement('div');
    wrap.id = 'prof-confirm-modal-wrap';
    wrap.className = 'pcm-backdrop';
    wrap.innerHTML = `
        <div class="pcm-modal" role="dialog" aria-modal="true" aria-labelledby="pcm-title">
            <div class="pcm-icon pcm-icon--${confirmClass}">
                <i class="fas ${confirmIcon}"></i>
            </div>
            <div class="pcm-title" id="pcm-title">${title}</div>
            <p class="pcm-message">${message}</p>
            <div class="pcm-actions">
                <button class="pcm-btn pcm-btn--confirm pcm-btn--${confirmClass}" id="pcm-confirm-btn">
                    <i class="fas ${confirmIcon}"></i> ${confirmLabel}
                </button>
                <button class="pcm-btn pcm-btn--cancel" id="pcm-cancel-btn">Cancel</button>
            </div>
        </div>`;

    document.body.appendChild(wrap);
    requestAnimationFrame(() => wrap.classList.add('pcm-open'));

    function close() {
        wrap.classList.remove('pcm-open');
        wrap.addEventListener('transitionend', () => wrap.remove(), { once: true });
    }

    document.getElementById('pcm-cancel-btn').addEventListener('click', close);
    wrap.addEventListener('click', e => { if (e.target === wrap) close(); });
    document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });

    document.getElementById('pcm-confirm-btn').addEventListener('click', () => {
        close();
        onConfirm();
    });
}

/* ────────────────────────────────────────────────────────────
   EDUCATION — DELETE (custom modal)
   ──────────────────────────────────────────────────────────── */

function confirmDeleteEducation(formEl, school) {
    showConfirmModal({
        title: 'Remove Education',
        message: `Are you sure you want to remove <strong>${escapeHtml(school)}</strong> from your education history?`,
        confirmLabel: 'Remove Education',
        confirmClass: 'danger',
        confirmIcon: 'fa-trash',
        onConfirm: () => formEl.submit()
    });
}

/* ────────────────────────────────────────────────────────────
   PORTFOLIO — DELETE (custom modal)
   ──────────────────────────────────────────────────────────── */

function confirmDeletePortfolio(formEl) {
    showConfirmModal({
        title: 'Remove Portfolio File',
        message: 'Are you sure you want to remove your portfolio file? This action cannot be undone.',
        confirmLabel: 'Remove Portfolio',
        confirmClass: 'danger',
        confirmIcon: 'fa-trash',
        onConfirm: () => formEl.submit()
    });
}

/* ────────────────────────────────────────────────────────────
   PORTFOLIO — TOGGLE FILE vs LINK MODE
   ──────────────────────────────────────────────────────────── */

function switchPortfolioMode(mode) {
    const fileTab   = document.getElementById('port-tab-file');
    const linkTab   = document.getElementById('port-tab-link');
    const filePanel = document.getElementById('port-panel-file');
    const linkPanel = document.getElementById('port-panel-link');
    if (!fileTab) return;

    if (mode === 'file') {
        fileTab.classList.add('active');
        linkTab.classList.remove('active');
        filePanel.style.display = '';
        linkPanel.style.display = 'none';
    } else {
        linkTab.classList.add('active');
        fileTab.classList.remove('active');
        linkPanel.style.display = '';
        filePanel.style.display = 'none';
    }
}

/* ────────────────────────────────────────────────────────────
   FILE VALIDATION — portfolio, certificates
   Shows the custom doc-error-overlay modal instead of the
   browser's default error page / form submission.
   ──────────────────────────────────────────────────────────── */

let _retryInputId  = null;
let _retryAccept   = null;
let _retryMaxMB    = null;
let _retryFormId   = null;

function showDocError(message, inputId, allowedExts, maxMB, formId) {
    _retryInputId = inputId;
    _retryAccept  = allowedExts;
    _retryMaxMB   = maxMB;
    _retryFormId  = formId;

    const msgEl   = document.getElementById('doc-error-message');
    const overlay = document.getElementById('doc-error-overlay');
    if (!msgEl || !overlay) {
        // Fallback — overlay missing from DOM; show a plain alert
        alert('File error: ' + message);
        return;
    }
    msgEl.textContent = message;
    overlay.classList.add('open');
}

function closeDocError() {
    const overlay = document.getElementById('doc-error-overlay');
    if (overlay) overlay.classList.remove('open');
    _retryInputId = _retryAccept = _retryMaxMB = _retryFormId = null;
}

function retryDocUpload() {
    closeDocError();
    if (!_retryInputId) return;
    const input  = document.getElementById(_retryInputId);
    if (!input) return;
    const exts   = _retryAccept;
    const maxMB  = _retryMaxMB;
    const formId = _retryFormId;
    input.value  = '';
    input.onchange = () => validateAndSubmit(input, exts, maxMB, formId);
    input.click();
}

/**
 * Validates a file chosen by the user, then submits a hidden form.
 * Always prevents the actual form submission when validation fails —
 * the error modal is shown instead of navigating away.
 */
function validateAndSubmit(inputEl, allowedExt, maxMB, formId) {
    const file = inputEl.files && inputEl.files[0];
    if (!file) return;

    const ext    = file.name.split('.').pop().toLowerCase();
    const sizeMB = file.size / (1024 * 1024);
    const hiddenInputId = formId.replace('form-', 'hidden-');

    if (!allowedExt.includes(ext)) {
        const allowed = allowedExt.map(e => e.toUpperCase()).join(', ');
        // Clear the input BEFORE showing the error so no submit can sneak through
        inputEl.value = '';
        showDocError(
            `"${escapeHtml(file.name)}" is not a supported file type. Please upload a ${allowed} file.`,
            inputEl.id, allowedExt, maxMB, formId
        );
        return;
    }

    if (sizeMB > maxMB) {
        inputEl.value = '';
        showDocError(
            `"${escapeHtml(file.name)}" is ${sizeMB.toFixed(1)} MB, which exceeds the ${maxMB} MB limit. Please choose a smaller file.`,
            inputEl.id, allowedExt, maxMB, formId
        );
        return;
    }

    // Validation passed — copy to the hidden form input and submit
    const dt = new DataTransfer();
    dt.items.add(file);
    const hiddenInput = document.getElementById(hiddenInputId);
    if (hiddenInput) hiddenInput.files = dt.files;
    document.getElementById(formId).submit();
}

function handleDrop(event, hiddenFieldName, allowedExt, maxMB) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');

    const file = event.dataTransfer && event.dataTransfer.files[0];
    if (!file) return;

    let targetForm   = null;
    let targetHidden = null;
    let visibleInput = null;

    document.querySelectorAll('form[style*="display:none"], form[style*="display: none"]').forEach(f => {
        const inp = f.querySelector('input[type="file"]');
        if (inp && inp.name === hiddenFieldName) {
            targetForm   = f;
            targetHidden = inp;
        }
    });

    const zone = event.currentTarget;
    const nearestInput = zone.parentElement
        ? zone.parentElement.querySelector('input[type="file"]:not([style*="display:none"])')
        : null;
    if (nearestInput) visibleInput = nearestInput;

    if (!targetForm || !targetHidden) return;

    const ext    = file.name.split('.').pop().toLowerCase();
    const sizeMB = file.size / (1024 * 1024);

    if (!allowedExt.includes(ext)) {
        const allowed = allowedExt.map(e => e.toUpperCase()).join(', ');
        showDocError(
            `"${escapeHtml(file.name)}" is not a supported file type. Please upload a ${allowed} file.`,
            visibleInput ? visibleInput.id : null,
            allowedExt, maxMB, targetForm.id
        );
        return;
    }

    if (sizeMB > maxMB) {
        showDocError(
            `"${escapeHtml(file.name)}" is ${sizeMB.toFixed(1)} MB, which exceeds the ${maxMB} MB limit. Please choose a smaller file.`,
            visibleInput ? visibleInput.id : null,
            allowedExt, maxMB, targetForm.id
        );
        return;
    }

    const dt = new DataTransfer();
    dt.items.add(file);
    targetHidden.files = dt.files;
    targetForm.submit();
}

/* ────────────────────────────────────────────────────────────
   UTILITY — Escape HTML to prevent XSS
   ──────────────────────────────────────────────────────────── */

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/* ────────────────────────────────────────────────────────────
   DRAG & DROP — Setup zones
   ──────────────────────────────────────────────────────────── */

function setupDragDropZones() {
    document.querySelectorAll('.doc-upload-zone').forEach(zone => {
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', function(e) {
            this.classList.remove('drag-over');
        });
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            const hiddenFieldName = this.closest('.port-add-section') 
                ? 'portfolio_file' 
                : (this.querySelector('input[type="file"]')?.name || 'file');
            handleDrop(e, hiddenFieldName, ['pdf', 'jpg', 'jpeg', 'png'], 10);
        });
    });
}

/* ────────────────────────────────────────────────────────────
   ON DOM READY
   ──────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
    // Force-close all edit/add forms on load
    document.querySelectorAll('.prof-edit-form, .prof-add-form').forEach(form => {
        form.style.display = 'none';
        form.dataset.open = 'false';
    });

    // Force-show all view panels on load
    document.querySelectorAll('[id^="view-"]').forEach(view => {
        view.style.display = '';
    });

    // Force-hide crop modal on load
    const pfpBackdrop = document.getElementById('pfpCropBackdrop');
    if (pfpBackdrop && !pfpBackdrop.classList.contains('active')) {
        pfpBackdrop.style.display = 'none';
    }

    // Initialise all custom checkboxes
    initCustomCheckboxes();

    // Stagger card entrance animation
    document.querySelectorAll('.prof-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(12px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 80 * index);
    });

    // Setup drag & drop zones for portfolio upload
    setupDragDropZones();

    // Fix for social view (sidebar) - ensure it's visible
    const socialView = document.getElementById('view-social');
    if (socialView) socialView.style.display = '';

    // Handle "currently studying" checkbox on existing forms
    document.querySelectorAll('.prof-checkbox-label input[type="checkbox"]').forEach(checkbox => {
        if (checkbox.name === 'is_current') {
            const endDateInput = checkbox.closest('.prof-form-grid')?.querySelector('input[name="end_date"]');
            if (endDateInput) {
                endDateInput.disabled = checkbox.checked;
                if (checkbox.checked) endDateInput.value = '';
            }
        }
    });
});