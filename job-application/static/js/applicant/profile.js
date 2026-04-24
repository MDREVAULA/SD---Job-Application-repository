/* ============================================================
   APPLICANT PROFILE JS
   ============================================================ */

// Toggle inline edit forms (personal info, social links)
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

    // Force-close all edit/add forms on load
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
   FILE VALIDATION — portfolio, certificates
   ============================================================ */

// ── Error popup helpers ────────────────────────────────────
let _retryInputId  = null;
let _retryAccept   = null;
let _retryMaxMB    = null;
let _retryFormId   = null;

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
    const input = document.getElementById(_retryInputId);
    if (!input) return;
    const exts   = _retryAccept;
    const maxMB  = _retryMaxMB;
    const formId = _retryFormId;
    input.value  = '';
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

    const ext    = file.name.split('.').pop().toLowerCase();
    const sizeMB = file.size / (1024 * 1024);

    // Determine the matching hidden input id from the form id
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

    // Find the correct hidden form based on field name
    let targetForm   = null;
    let targetHidden = null;
    let visibleInput = null;

    // Search all forms on the page for one with matching field name
    document.querySelectorAll('form[style*="display:none"], form[style*="display: none"]').forEach(f => {
        const inp = f.querySelector('input[type="file"]');
        if (inp && inp.name === hiddenFieldName) {
            targetForm   = f;
            targetHidden = inp;
        }
    });

    // Also grab the visible input closest to the drop zone (for error retry)
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