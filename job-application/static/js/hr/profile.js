/* ============================================================
   HR PROFILE JS
   ============================================================ */

// Toggle inline edit forms
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

    // Update ALL buttons that target this section
    document.querySelectorAll('[data-edit-target="' + section + '"]').forEach(btn => {
        btn.innerHTML = isEditing
            ? '<i class="fas fa-pen"></i> Edit'
            : '<i class="fas fa-times"></i> Cancel';
    });
}

// On page load
document.addEventListener('DOMContentLoaded', function () {

    // Force-close all edit forms on load
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