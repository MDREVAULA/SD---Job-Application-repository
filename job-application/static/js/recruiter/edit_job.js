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

// Additional JavaScript for the new design
document.addEventListener('DOMContentLoaded', function() {
  // Tab switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      tabBtns.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
    });
  });
  
  // Keep your existing image preview and delete functionality
  // They will work with the new design
});

// ===================================
// EDIT JOB — client-side functionality
// Handles: image delete, cover preview,
//          delete-job modal, drag-and-drop
// ===================================

// ===================================
// DELETE IMAGE MODAL
// ===================================

function openDeleteImageModal(imageId) {
    const modal      = document.getElementById('deleteImageModal');
    const confirmBtn = document.getElementById('confirmDeleteImageBtn');

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

window.addEventListener('click', function (e) {
    const imgModal = document.getElementById('deleteImageModal');
    if (imgModal && e.target === imgModal) closeDeleteImageModal();

    const jobModal = document.getElementById('deleteJobModal');
    if (jobModal && e.target === jobModal) closeDeleteJobModal();
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeDeleteImageModal();
        closeDeleteJobModal();
    }
});

// ===================================
// DELETE IMAGE — AJAX
// ===================================

function deleteImage(imageId) {
    const imageCard = document.getElementById('image-' + imageId);
    if (!imageCard) return;

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
            imageCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            imageCard.style.opacity    = '0';
            imageCard.style.transform  = 'scale(0.8)';
            setTimeout(() => imageCard.remove(), 300);
        } else {
            alert(data.error || 'Failed to delete image. Please try again.');
        }
    })
    .catch(() => alert('An error occurred while deleting the image.'));
}

// ===================================
// DRAG-AND-DROP for gallery upload zone
// ===================================
document.addEventListener('DOMContentLoaded', function () {
    const uploadZone = document.querySelector('#tab-gallery .upload-zone');
    const fileInput  = document.getElementById('posterInput');

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('dragover', e => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
        uploadZone.addEventListener('drop', e => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    // Cover photo drag-and-drop
    const coverContainer = document.getElementById('coverPhotoContainer');
    const coverInput     = document.getElementById('coverPhotoInput');
    if (coverContainer && coverInput) {
        coverContainer.addEventListener('dragover', e => {
            e.preventDefault();
            coverContainer.style.outline = '2px dashed #14b8a6';
        });
        coverContainer.addEventListener('dragleave', () => {
            coverContainer.style.outline = '';
        });
        coverContainer.addEventListener('drop', e => {
            e.preventDefault();
            coverContainer.style.outline = '';
            if (e.dataTransfer.files.length) {
                // Programmatically assign files to input
                const dt   = new DataTransfer();
                dt.items.add(e.dataTransfer.files[0]);
                coverInput.files = dt.files;
                previewCoverPhoto(coverInput);
            }
        });
    }
});