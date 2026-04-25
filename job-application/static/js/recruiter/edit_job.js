/* ─────────────────────────────────────────────
   UNSAVED CHANGES TRACKER
   ───────────────────────────────────────────── */
let _isDirty = false;
 
function markDirty() {
  if (_isDirty) return;
  _isDirty = true;
  /* Show the unsaved-changes banner */
  const banner = document.getElementById('unsavedBanner');
  if (banner) banner.style.display = 'flex';
}
 
function markClean() {
  _isDirty = false;
  const banner = document.getElementById('unsavedBanner');
  if (banner) banner.style.display = 'none';
}
 
/* Warn on browser back / close / refresh */
window.addEventListener('beforeunload', function (e) {
  if (_isDirty) {
    e.preventDefault();
    e.returnValue = '';   // Required for Chrome
  }
});
 
/* Intercept the "Cancel" link and every anchor that leaves the page */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('a[href]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (!_isDirty) return;
      const href = link.getAttribute('href');
      /* Ignore anchors, javascript:, and same-page hash links */
      if (!href || href.startsWith('#') || href.startsWith('javascript')) return;
      e.preventDefault();
      showLeaveModal(href);
    });
  });
});
 
function showLeaveModal(destination) {
  const modal = document.getElementById('leaveConfirmModal');
  if (!modal) {
    /* Fallback if modal markup isn't present */
    if (confirm('You have unsaved changes. Leave without saving?')) {
      markClean();
      window.location.href = destination;
    }
    return;
  }
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  document.getElementById('leaveConfirmBtn').onclick = function () {
    markClean();
    closeLeaveModal();
    window.location.href = destination;
  };
}
 
function closeLeaveModal() {
  const modal = document.getElementById('leaveConfirmModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}
 
 
/* ─────────────────────────────────────────────
   DELETE IMAGE MODAL
   ───────────────────────────────────────────── */
 
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
 
  const leaveModal = document.getElementById('leaveConfirmModal');
  if (leaveModal && e.target === leaveModal) closeLeaveModal();
});
 
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    closeDeleteImageModal();
    closeDeleteJobModal();
    closeLeaveModal();
  }
});
 
 
/* ─────────────────────────────────────────────
   DELETE IMAGE — AJAX (this is immediate; deleting
   an existing image is a committed action, not a
   "draft" change, so it fires right away)
   ───────────────────────────────────────────── */
 
function deleteImage(imageId) {
  const imageCard = document.getElementById('image-' + imageId);
  if (!imageCard) return;
 
// In deleteImage(), replace the fetch headers:
  fetch('/recruiter/delete-job-image/' + imageId, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
      },
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        imageCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        imageCard.style.opacity    = '0';
        imageCard.style.transform  = 'scale(0.8)';
        setTimeout(function () { imageCard.remove(); }, 300);
      } else {
        alert(data.error || 'Failed to delete image. Please try again.');
      }
    })
    .catch(function () { alert('An error occurred while deleting the image.'); });
}
 
 
/* ─────────────────────────────────────────────
   DRAG-AND-DROP (gallery + cover photo)
   ───────────────────────────────────────────── */
 
document.addEventListener('DOMContentLoaded', function () {
  const uploadZone = document.querySelector('#tab-gallery .upload-zone');
  const fileInput  = document.getElementById('posterInput');
 
  if (uploadZone && fileInput) {
    uploadZone.addEventListener('dragover', function (e) {
      e.preventDefault();
      uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', function () {
      uploadZone.classList.remove('drag-over');
    });
    uploadZone.addEventListener('drop', function (e) {
      e.preventDefault();
      uploadZone.classList.remove('drag-over');
      fileInput.files = e.dataTransfer.files;
      fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      markDirty();
    });
  }
 
  /* Cover photo drag-and-drop */
  const coverContainer = document.getElementById('coverPhotoContainer');
  const coverInput     = document.getElementById('coverPhotoInput');
  if (coverContainer && coverInput) {
    coverContainer.addEventListener('dragover', function (e) {
      e.preventDefault();
      coverContainer.style.outline = '2px dashed #14b8a6';
    });
    coverContainer.addEventListener('dragleave', function () {
      coverContainer.style.outline = '';
    });
    coverContainer.addEventListener('drop', function (e) {
      e.preventDefault();
      coverContainer.style.outline = '';
      if (e.dataTransfer.files.length) {
        const dt = new DataTransfer();
        dt.items.add(e.dataTransfer.files[0]);
        coverInput.files = dt.files;
        previewCoverPhoto(coverInput);
        markDirty();
      }
    });
  }
 
  /* Mark dirty whenever any native form field changes */
  const mainForm = document.getElementById('editJobForm');
  if (mainForm) {
    mainForm.addEventListener('input',  function () { markDirty(); });
    mainForm.addEventListener('change', function () { markDirty(); });
  }
 
  /* Mark clean when the form actually submits (saving) */
  if (mainForm) {
    mainForm.addEventListener('submit', function () { markClean(); });
  }
});