// ============================================
// Save / Unsave Job Toggle
// Used on: jobs.html, job_details.html
// ============================================

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function toggleSaveJob(btn, jobId) {
    const isAuth = btn.dataset.auth === 'true';
    if (!isAuth) {
        window.location.href = '/login';
        return;
    }

    // Prevent double-clicks
    if (btn.dataset.loading === 'true') return;
    btn.dataset.loading = 'true';

    fetch('/applicant/save-job/' + jobId, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const allBtns = document.querySelectorAll(`[data-job-id="${jobId}"]`);
            allBtns.forEach(function (b) {
                const icon = b.querySelector('i');
                const svgFill = b.querySelector('svg');
                const span = b.querySelector('span');

                if (data.saved) {
                    if (icon) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                    }
                    if (svgFill) svgFill.setAttribute('fill', 'currentColor');
                    if (span) span.textContent = b.classList.contains('btn-sidebar-save') ? 'Saved' : 'Saved';
                    b.classList.add('saved');
                    b.title = 'Saved';
                } else {
                    if (icon) {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                    }
                    if (svgFill) svgFill.setAttribute('fill', 'none');
                    if (span) span.textContent = b.classList.contains('btn-sidebar-save') ? 'Save for Later' : 'Save';
                    b.classList.remove('saved');
                    b.title = 'Save this job';
                }
                b.dataset.loading = 'false';
            });
        }
    })
    .catch(() => {
        btn.dataset.loading = 'false';
    });
}

// ============================================
// Unsave Job (used on saved_jobs.html cards)
// ============================================

function unsaveJob(btn, jobId) {
    if (btn.dataset.loading === 'true') return;
    btn.dataset.loading = 'true';

    fetch('/applicant/save-job/' + jobId, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
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
                // Update the count in the header
                const countEl = document.getElementById('savedCount');
                const remaining = document.querySelectorAll('.saved-card').length;
                if (countEl) countEl.textContent = remaining + ' job' + (remaining !== 1 ? 's' : '');
                if (remaining === 0) location.reload();
            }, 300);
        } else {
            btn.dataset.loading = 'false';
        }
    })
    .catch(() => {
        btn.dataset.loading = 'false';
    });
}