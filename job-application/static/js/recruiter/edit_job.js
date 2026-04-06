// ===================================
// EDIT JOB — Image Delete Only
// (drag & drop is handled by job_posting.js)
// ===================================

// ===================================
// DELETE IMAGE MODAL
// ===================================

function openDeleteImageModal(imageId) {
    const modal      = document.getElementById('deleteImageModal');
    const confirmBtn = document.getElementById('confirmDeleteImageBtn');

    // Assign the specific image ID to the confirm button
    confirmBtn.onclick = function () {
        deleteImage(imageId);
        closeDeleteImageModal();
    };

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeDeleteImageModal() {
    const modal = document.getElementById('deleteImageModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close when clicking backdrop
window.addEventListener('click', function (e) {
    const modal = document.getElementById('deleteImageModal');
    if (modal && e.target === modal) closeDeleteImageModal();
});

// Close on ESC
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeDeleteImageModal();
});

// ===================================
// DELETE IMAGE — AJAX FETCH
// ===================================

function deleteImage(imageId) {
    const imageCard = document.getElementById('image-' + imageId);
    if (!imageCard) return;

    const btn = imageCard.querySelector('.remove-btn');
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        btn.disabled = true;
    }

    fetch('/recruiter/delete-job-image/' + imageId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Animate out and remove the card
            imageCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            imageCard.style.opacity    = '0';
            imageCard.style.transform  = 'scale(0.8)';
            setTimeout(() => imageCard.remove(), 300);
        } else {
            alert(data.error || 'Failed to delete image. Please try again.');
            if (btn) {
                btn.innerHTML = '';
                btn.disabled  = false;
            }
        }
    })
    .catch(() => {
        alert('An error occurred while deleting the image.');
        if (btn) {
            btn.innerHTML = '';
            btn.disabled  = false;
        }
    });
}