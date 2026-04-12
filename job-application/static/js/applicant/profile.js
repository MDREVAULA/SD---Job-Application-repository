/* ============================================================
   APPLICANT PROFILE JS — Fixed toggle logic
   ============================================================ */

// Toggle inline edit forms (personal info, social links)
function toggleEdit(section) {
    const view = document.getElementById('view-' + section);
    const form = document.getElementById('edit-' + section);
    if (!view || !form) return;

    // Use a data attribute as the source of truth instead of style.display
    // because style.display is '' (not 'none') after a page reload
    const isEditing = form.dataset.open === 'true';

    if (isEditing) {
        // Close: show view, hide form
        form.dataset.open = 'false';
        form.style.display = 'none';
        view.style.display = '';
    } else {
        // Open: hide view, show form
        form.dataset.open = 'true';
        form.style.display = '';
        view.style.display = 'none';
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Update ALL buttons that target this section (header + card)
    document.querySelectorAll('[data-edit-target="' + section + '"]').forEach(btn => {
        btn.innerHTML = isEditing
            ? '<i class="fas fa-pen"></i> Edit'
            : '<i class="fas fa-times"></i> Cancel';
    });
}

// Toggle add forms (experience, education, skills, etc.)
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

// Disable/enable end date when "currently working/studying" is checked
function toggleEndDate(endDateId, checkbox) {
    const endDate = document.getElementById(endDateId);
    if (!endDate) return;
    endDate.disabled = checkbox.checked;
    if (checkbox.checked) endDate.value = '';
}

// On page load — make sure all forms are properly closed
document.addEventListener('DOMContentLoaded', function () {

    // Force-close all edit forms on load (fixes the page-reload stuck state)
    document.querySelectorAll('.prof-edit-form, .prof-add-form').forEach(form => {
        form.style.display = 'none';
        form.dataset.open = 'false';
    });

    // Force-show all view panels on load
    document.querySelectorAll('[id^="view-"]').forEach(view => {
        view.style.display = '';
    });

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
});

/* ============================================================
   DOCUMENTS TAB — switching, validation, drag-drop, error popup
   ============================================================ */

// ── Tab switching ──────────────────────────────────────────
function switchDocTab(tab, btn) {
    // Hide all panels
    document.querySelectorAll('.doc-tab-panel').forEach(p => p.style.display = 'none');
    // Deactivate all tab buttons
    document.querySelectorAll('.doc-tab').forEach(b => b.classList.remove('active'));
    // Show target panel
    const panel = document.getElementById('doctab-' + tab);
    if (panel) panel.style.display = '';
    // Activate clicked button
    if (btn) btn.classList.add('active');
}

// ── Error popup helpers ────────────────────────────────────
let _retryInputId  = null;   // which file input to re-trigger
let _retryAccept   = null;   // accepted extensions list
let _retryMaxMB    = null;   // size cap in MB
let _retryFormId   = null;   // form to submit after re-pick

function showDocError(message, inputId, allowedExts, maxMB, formId) {
    _retryInputId = inputId;
    _retryAccept  = allowedExts;
    _retryMaxMB   = maxMB;
    _retryFormId  = formId;

    document.getElementById('doc-error-message').textContent = message;
    document.getElementById('doc-error-overlay').classList.add('open');
}

function closeDocError() {
    document.getElementById('doc-error-overlay').classList.remove('open');
    _retryInputId = _retryAccept = _retryMaxMB = _retryFormId = null;
}

function retryDocUpload() {
    closeDocError();
    if (!_retryInputId) return;
    // Re-bind a fresh onchange on the visible input, then click
    const input = document.getElementById(_retryInputId);
    if (!input) return;
    const exts   = _retryAccept;
    const maxMB  = _retryMaxMB;
    const formId = _retryFormId;
    input.value  = '';   // clear so same file triggers change
    input.onchange = () => validateAndSubmit(input, exts, maxMB, formId);
    input.click();
}

// ── Core validator ─────────────────────────────────────────
// inputEl    — the <input type="file"> that fired
// allowedExt — e.g. ['pdf'] or ['pdf','jpg','jpeg','png']
// maxMB      — numeric cap
// formId     — id of the hidden <form> to submit on success
function validateAndSubmit(inputEl, allowedExt, maxMB, formId) {
    const file = inputEl.files && inputEl.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    const sizeMB = file.size / (1024 * 1024);

    // Determine the matching hidden input id from the form
    const hiddenInputId = formId.replace('form-', 'hidden-');

    // Wrong type?
    if (!allowedExt.includes(ext)) {
        const allowed = allowedExt.map(e => e.toUpperCase()).join(', ');
        showDocError(
            `"${file.name}" is not a supported file type. Please upload a ${allowed} file.`,
            inputEl.id, allowedExt, maxMB, formId
        );
        inputEl.value = '';
        return;
    }

    // Too big?
    if (sizeMB > maxMB) {
        showDocError(
            `"${file.name}" is ${sizeMB.toFixed(1)} MB, which exceeds the ${maxMB} MB limit. Please choose a smaller file.`,
            inputEl.id, allowedExt, maxMB, formId
        );
        inputEl.value = '';
        return;
    }

    // All good — copy to hidden input and submit
    const dt = new DataTransfer();
    dt.items.add(file);
    const hiddenInput = document.getElementById(hiddenInputId);
    if (hiddenInput) hiddenInput.files = dt.files;

    document.getElementById(formId).submit();
}

// ── Drag & drop handler ────────────────────────────────────
// Called from ondrop on the drop zone div
function handleDrop(event, hiddenFieldName, allowedExt, maxMB) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');

    const file = event.dataTransfer && event.dataTransfer.files[0];
    if (!file) return;

    // Find the form whose hidden input has the matching name
    const forms = document.querySelectorAll('.doc-tab-panel:not([style*="none"]) form');
    let targetForm = null;
    let targetHidden = null;
    let visibleInput = null;

    forms.forEach(f => {
        const inp = f.querySelector('input[type="file"]');
        if (inp && inp.name === hiddenFieldName) {
            targetForm   = f;
            targetHidden = inp;
        }
    });

    // Also grab the visible input (for error retry)
    const panel = event.currentTarget.closest('.doc-tab-panel');
    if (panel) visibleInput = panel.querySelector('input[type="file"]:not([style*="none"])');

    if (!targetForm || !targetHidden) return;

    const ext    = file.name.split('.').pop().toLowerCase();
    const sizeMB = file.size / (1024 * 1024);

    if (!allowedExt.includes(ext)) {
        const allowed = allowedExt.map(e => e.toUpperCase()).join(', ');
        showDocError(
            `"${file.name}" is not a supported file type. Please upload a ${allowed} file.`,
            visibleInput ? visibleInput.id : null,
            allowedExt, maxMB, targetForm.id
        );
        return;
    }

    if (sizeMB > maxMB) {
        showDocError(
            `"${file.name}" is ${sizeMB.toFixed(1)} MB, which exceeds the ${maxMB} MB limit. Please choose a smaller file.`,
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