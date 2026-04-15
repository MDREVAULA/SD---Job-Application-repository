// ============================================
// Save / Unsave Job Toggle
// Used on: index.html, job_details.html
// ============================================

function toggleSaveJob(btn, jobId) {
    const isAuth = btn.dataset.auth === 'true';
    if (!isAuth) {
        window.location.href = '/login';
        return;
    }

    fetch('/applicant/save-job/' + jobId, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Sync ALL bookmark buttons on the page for this same job
            // (handles header btn + sidebar btn both updating at once)
            const allBtns = document.querySelectorAll(`[data-job-id="${jobId}"]`);
            allBtns.forEach(function (b) {
                const icon = b.querySelector('i');
                const span = b.querySelector('span');

                if (data.saved) {
                    if (icon) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                    }
                    if (span) {
                        span.textContent = b.classList.contains('btn-sidebar-save')
                            ? 'Saved'
                            : 'Saved';
                    }
                    b.classList.add('saved');
                    b.title = 'Saved';
                } else {
                    if (icon) {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                    }
                    if (span) {
                        span.textContent = b.classList.contains('btn-sidebar-save')
                            ? 'Save for Later'
                            : 'Save';
                    }
                    b.classList.remove('saved');
                    b.title = 'Save this job';
                }
            });
        }
    })
    .catch(() => {});
}

// ============================================
// Unsave Job (used on saved_jobs.html cards)
// ============================================

function unsaveJob(btn, jobId) {
    fetch('/applicant/save-job/' + jobId, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && !data.saved) {
            const card = btn.closest('.saved-card');
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            setTimeout(() => {
                card.remove();
                if (document.querySelectorAll('.saved-card').length === 0) {
                    location.reload();
                }
            }, 300);
        }
    })
    .catch(() => {});
}