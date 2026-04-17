let deleteFormToSubmit = null;
let deleteJobId = null;
let deleteHasApplicants = false;

function openDeleteModal(button) {
    const modal = document.getElementById('deleteModal');

    // Guard: if modal element doesn't exist, fail loudly
    if (!modal) {
        console.error('deleteModal element not found in DOM');
        return;
    }

    const form = button.closest('form');
    const row  = button.closest('tr');

    deleteFormToSubmit  = form;

    // Works for both full URL and relative path
    const actionUrl     = form ? form.getAttribute('action') : '';
    const match         = actionUrl.match(/delete-job\/(\d+)/);
    deleteJobId         = match ? match[1] : null;
    deleteHasApplicants = parseInt(row?.dataset?.applicants || '0') > 0;

    const warningEl = document.getElementById('deleteWarning');
    const normalMsg = document.getElementById('deleteNormalMsg');

    if (deleteHasApplicants) {
        if (warningEl) warningEl.style.display = 'block';
        if (normalMsg) normalMsg.style.display = 'none';
    } else {
        if (warningEl) warningEl.style.display = 'none';
        if (normalMsg) normalMsg.style.display = 'block';
    }

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    deleteFormToSubmit  = null;
    deleteJobId         = null;
    deleteHasApplicants = false;
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const modal      = document.getElementById('deleteModal');

    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            if (!deleteJobId) return;

            if (deleteHasApplicants) {
                confirmBtn.disabled    = true;
                confirmBtn.textContent = 'Deleting…';

                try {
                    const res  = await fetch(`/recruiter/force-delete-job/${deleteJobId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                    });
                    const data = await res.json();

                    if (data.success) {
                        const row = deleteFormToSubmit?.closest('tr');
                        if (row) row.remove();
                        closeDeleteModal();
                    } else {
                        alert('Delete failed: ' + (data.error || 'Unknown error'));
                        confirmBtn.disabled    = false;
                        confirmBtn.textContent = 'Delete permanently';
                    }
                } catch (err) {
                    alert('Network error. Please try again.');
                    confirmBtn.disabled    = false;
                    confirmBtn.textContent = 'Delete permanently';
                }
            } else {
                deleteFormToSubmit.submit();
            }
        });
    }

    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeDeleteModal();
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeDeleteModal();
    });
});