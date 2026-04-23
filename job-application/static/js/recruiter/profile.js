function toggleEdit(section) {
    const view = document.getElementById('view-' + section);
    const form = document.getElementById('edit-' + section);
    if (!view || !form) return;

    const isEditing = form.dataset.open === 'true';

    if (isEditing) {
        form.dataset.open = 'false';
        form.style.display = 'none';
        view.style.display = 'block';      // ← explicit 'block' not ''
    } else {
        form.dataset.open = 'true';
        form.style.display = 'block';      // ← explicit 'block' not ''
        view.style.display = 'none';
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    document.querySelectorAll('[data-edit-target="' + section + '"][data-edit-label]').forEach(btn => {
        const label = btn.dataset.editLabel || 'Edit';
        btn.innerHTML = isEditing
            ? `<i class="fas fa-pen"></i> ${label}`
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
        form.style.display = 'block';     // ← explicit 'block' not ''
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function toggleEndDate(endDateId, checkbox) {
    const endDate = document.getElementById(endDateId);
    if (!endDate) return;
    endDate.disabled = checkbox.checked;
    if (checkbox.checked) endDate.value = '';
}

document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.prof-edit-form, .prof-add-form').forEach(form => {
        form.style.display = 'none';
        form.dataset.open = 'false';
    });

    document.querySelectorAll('.prof-view').forEach(view => {
        view.style.display = 'block';
    });

    const socialView = document.getElementById('view-social');
    if (socialView) socialView.style.display = 'block';

    const pfpBackdrop  = document.getElementById('pfpCropBackdrop');
    const logoBackdrop = document.getElementById('logoCropBackdrop');
    if (pfpBackdrop  && !pfpBackdrop.classList.contains('active'))  pfpBackdrop.style.display = 'none';
    if (logoBackdrop && !logoBackdrop.classList.contains('active')) logoBackdrop.style.display = 'none';

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