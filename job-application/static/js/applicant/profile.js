/* ============================================================
   APPLICANT PROFILE JS
   ============================================================ */

// Toggle inline edit forms (personal info, social links)
function toggleEdit(section) {
    const view = document.getElementById('view-' + section);
    const form = document.getElementById('edit-' + section);
    if (!view || !form) return;

    const isEditing = form.style.display !== 'none';
    view.style.display = isEditing ? '' : 'none';
    form.style.display = isEditing ? 'none' : '';

    // Update button text
    const btn = document.querySelector('#section-' + section + ' .prof-edit-btn');
    if (btn) {
        btn.innerHTML = isEditing
            ? '<i class="fas fa-pen"></i> Edit'
            : '<i class="fas fa-times"></i> Cancel';
    }
}

// Toggle add forms (experience, education, skills, etc.)
function toggleAddForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    const isVisible = form.style.display !== 'none';
    form.style.display = isVisible ? 'none' : '';

    if (!isVisible) {
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

// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function () {
    // Stagger card entrance
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