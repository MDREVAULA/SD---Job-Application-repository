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
