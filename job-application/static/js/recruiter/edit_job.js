/* ─────────────────────────────────────────────
   UNSAVED CHANGES TRACKER
   ───────────────────────────────────────────── */
let _isDirty = false;

function markDirty() {
  if (_isDirty) return;
  _isDirty = true;
  const banner = document.getElementById('unsavedBanner');
  if (banner) banner.style.display = 'flex';
}

function markClean() {
  _isDirty = false;
  const banner = document.getElementById('unsavedBanner');
  if (banner) banner.style.display = 'none';
}

window.addEventListener('beforeunload', function (e) {
  if (_isDirty) {
    e.preventDefault();
    e.returnValue = '';
  }
});

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('a[href]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (!_isDirty) return;
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript')) return;
      e.preventDefault();
      showLeaveModal(href);
    });
  });
});

function showLeaveModal(destination) {
  const modal = document.getElementById('leaveConfirmModal');
  if (!modal) {
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
   DELETE IMAGE — AJAX
   ───────────────────────────────────────────── */

function deleteImage(imageId) {
  const imageCard = document.getElementById('image-' + imageId);
  if (!imageCard) return;

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

  const mainForm = document.getElementById('editJobForm');
  if (mainForm) {
    mainForm.addEventListener('input',  function () { markDirty(); });
    mainForm.addEventListener('change', function () { markDirty(); });
    mainForm.addEventListener('submit', function () { markClean(); });
  }
});


/* ═══════════════════════════════════════════════════════════
   TOAST HELPER
   ═══════════════════════════════════════════════════════════ */
function showToast(msg, isError) {
  const toast = document.getElementById('saveToast');
  if (!toast) return;
  document.getElementById('saveToastMsg').textContent = msg;
  toast.style.display    = 'flex';
  toast.style.borderColor = isError ? '#ef4444' : '#14b8a6';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(function () { toast.style.display = 'none'; }, 3000);
}


/* ═══════════════════════════════════════════════════════════
   ALLOW-APPLICATIONS TOGGLE (nav bar)
   ═══════════════════════════════════════════════════════════ */
function handleAllowToggle(checkbox) {
  /* If the toggle is locked due to deadline/quota, reject the change */
  if (checkbox.disabled) return;

  const allowed = checkbox.checked;
  const badge      = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');
  badge.classList.toggle('btn-published',  allowed);
  badge.classList.toggle('btn-closed',    !allowed);
  statusText.textContent = allowed ? 'Published' : 'Closed';
  document.getElementById('allowApplicationsHidden').value = allowed ? 'on' : '';
  markDirty();
}


/* ═══════════════════════════════════════════════════════════
   DEADLINE + QUOTA → AUTO-LOCK ALL ALLOW-APPLICATIONS TOGGLES
   Targets: nav toggle (#allowApplicationsToggle) AND
            every sidebar toggle (input[name="allow_applications"])
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {
  const dateInput  = document.querySelector('input[name="expiration_date"]');
  const hidden     = document.getElementById('allowApplicationsHidden');
  const badge      = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');

  /* Read quota state injected by the template via data attributes on <body>
     or fall back to reading the DOM directly.
     We expose these via data-* on the form element to avoid an extra inline script. */
  const form        = document.getElementById('editJobForm');
  const quotaFull   = form ? form.dataset.quotaFull === 'true'   : false;
  const isExpired   = form ? form.dataset.isExpired === 'true'   : false;

  function getAllToggles() {
    return Array.from(document.querySelectorAll(
      '#allowApplicationsToggle, input[name="allow_applications"]'
    ));
  }

  /* Inject warning label into nav toggle wrapper (once) */
  const navWrapper = document.querySelector('.allow-toggle-wrapper');
  let warningSpan  = document.getElementById('deadlineWarning');
  if (!warningSpan && navWrapper) {
    warningSpan = document.createElement('span');
    warningSpan.id = 'deadlineWarning';
    warningSpan.style.cssText =
      'font-size:11px;color:#dc2626;font-weight:600;margin-left:6px;display:none;white-space:nowrap;';
    navWrapper.appendChild(warningSpan);
  }

  function lockAll(reason) {
    getAllToggles().forEach(function (t) {
      t.checked  = false;
      t.disabled = true;
      t.style.opacity = '0.45';
      const lbl = t.closest('label');
      if (lbl) { lbl.style.pointerEvents = 'none'; lbl.style.opacity = '0.45'; }
    });
    if (hidden)      hidden.value            = '';
    if (badge)      { badge.classList.remove('btn-published'); badge.classList.add('btn-closed'); }
    if (statusText)  statusText.textContent   = 'Closed';
    if (warningSpan) {
      warningSpan.textContent  = reason === 'quota' ? 'Quota full' : 'Deadline passed';
      warningSpan.style.display = 'inline';
    }
  }

  function unlockAll() {
    getAllToggles().forEach(function (t) {
      t.disabled = false;
      t.style.opacity = '';
      const lbl = t.closest('label');
      if (lbl) { lbl.style.pointerEvents = ''; lbl.style.opacity = ''; }
    });
    if (warningSpan) warningSpan.style.display = 'none';
  }

  function evaluate() {
    /* Quota-full always wins regardless of date */
    if (quotaFull) { lockAll('quota'); return; }

    const val = dateInput ? dateInput.value : '';
    if (!val) { unlockAll(); return; }

    const today = new Date().toISOString().slice(0, 10);
    if (val < today) {
      lockAll('deadline');
    } else {
      unlockAll();
    }
  }

  if (dateInput) {
    dateInput.addEventListener('change', evaluate);
    dateInput.addEventListener('input',  evaluate);
  }

  evaluate();
});


/* ═══════════════════════════════════════════════════════════
   INLINE SECTION EDITORS (About, Values, Why Join Us)
   ═══════════════════════════════════════════════════════════ */

const _editSections = {
  about:   { display: 'aboutDisplay',   form: 'aboutEditForm'   },
  values:  { display: 'valuesDisplay',  form: 'valuesEditForm'  },
  whyjoin: { display: 'whyjoinDisplay', form: 'whyjoinEditForm' },
};

function toggleEditMode(section) {
  const s = _editSections[section];
  if (!s) return;
  const displayEl = document.getElementById(s.display);
  const formEl    = document.getElementById(s.form);
  const isEditing = formEl.style.display !== 'none';
  displayEl.style.display = isEditing ? '' : 'none';
  formEl.style.display    = isEditing ? 'none' : 'block';
}

/* ── About Company ── */
function saveAbout() {
  const content = document.getElementById('aboutTextarea').value;
  document.getElementById('aboutDisplay').innerHTML =
    content ? content.replace(/\n/g, '<br>') : '<p>(no content)</p>';
  document.getElementById('aboutCompanyFormField').value = content;
  toggleEditMode('about');
  markDirty();
  showToast('About company updated — click Save Changes to persist.');
}

/* ── Company Values ── */
function addValueRow(title, desc) {
  title = title || '';
  desc  = desc  || '';
  const row = document.createElement('div');
  row.className = 'value-editor-row';
  row.innerHTML =
    '<input type="text" class="input-text value-title-input" placeholder="Value title"'
    + ' value="' + _esc(title) + '" style="margin-bottom:6px;">'
    + '<input type="text" class="input-text value-desc-input" placeholder="Short description"'
    + ' value="' + _esc(desc) + '">'
    + '<button type="button" class="btn-remove-value" onclick="this.parentElement.remove()">×</button>';
  document.getElementById('valuesEditorList').appendChild(row);
}

function saveValues() {
  const rows  = document.querySelectorAll('.value-editor-row');
  const items = Array.from(rows).map(function (r) {
    return {
      title:       r.querySelector('.value-title-input').value.trim(),
      description: r.querySelector('.value-desc-input').value.trim(),
    };
  }).filter(function (v) { return v.title; });

  document.getElementById('valuesDisplay').innerHTML = items.map(function (v) {
    return '<div class="value-item">'
      + '<div class="value-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"'
      + ' stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div>'
      + '<div class="value-content">'
      + '<h5 class="value-title">'       + _esc(v.title)       + '</h5>'
      + '<p class="value-description">'  + _esc(v.description) + '</p>'
      + '</div></div>';
  }).join('');

  document.getElementById('companyValuesFormField').value = JSON.stringify(items);
  toggleEditMode('values');
  markDirty();
  showToast('Company values updated — click Save Changes to persist.');
}

/* ── Why Join Us ── */
function addBenefitRow(val) {
  val = val || '';
  const row = document.createElement('div');
  row.className = 'benefit-editor-row';
  row.innerHTML =
    '<input type="text" class="input-text benefit-input"'
    + ' value="' + _esc(val) + '" placeholder="e.g. Competitive salary">'
    + '<button type="button" class="btn-remove-value" onclick="this.parentElement.remove()">×</button>';
  document.getElementById('benefitsList').appendChild(row);
}

function saveWhyJoin() {
  const inputs = document.querySelectorAll('.benefit-input');
  const items  = Array.from(inputs).map(function (i) { return i.value.trim(); }).filter(Boolean);

  document.getElementById('whyjoinDisplay').innerHTML = items.map(function (b) {
    return '<div class="benefit-item">'
      + '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"'
      + ' stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'
      + '<span>' + _esc(b) + '</span></div>';
  }).join('');

  document.getElementById('whyJoinUsFormField').value = JSON.stringify(items);
  toggleEditMode('whyjoin');
  markDirty();
  showToast('Benefits updated — click Save Changes to persist.');
}


/* ═══════════════════════════════════════════════════════════
   HR TEAM MEMBER TOGGLE
   ═══════════════════════════════════════════════════════════ */

const _teamOriginal = {};
const _teamQueue    = {};

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.btn-assign-hr').forEach(function (btn) {
    const row = btn.closest('[data-hr-id]');
    if (!row) return;
    const hrId = parseInt(row.dataset.hrId, 10);
    _teamOriginal[hrId] = btn.dataset.assigned === 'true';
  });
});

function toggleTeamMember(jobId, hrId, btn) {
  const isAssigned  = btn.dataset.assigned === 'true';
  const nowAssigned = !isAssigned;

  btn.dataset.assigned = nowAssigned ? 'true' : 'false';
  btn.classList.toggle('assigned', nowAssigned);
  const row = document.getElementById('hrAssignRow-' + hrId);
  if (row) row.classList.toggle('assigned', nowAssigned);
  btn.innerHTML = nowAssigned
    ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
      + '<polyline points="20 6 9 17 4 12"/></svg> Assigned'
    : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
      + '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Assign';

  if (nowAssigned !== _teamOriginal[hrId]) {
    _teamQueue[hrId] = nowAssigned ? 'add' : 'remove';
  } else {
    delete _teamQueue[hrId];
  }

  markDirty();
  showToast((nowAssigned ? 'HR member marked for assignment' : 'HR member marked for removal')
    + ' — click Save Changes to persist.');
}

document.addEventListener('DOMContentLoaded', function () {
  const mainForm = document.getElementById('editJobForm');
  if (!mainForm) return;

  mainForm.addEventListener('submit', function (e) {
    const pending = Object.keys(_teamQueue);
    if (pending.length === 0) return;

    e.preventDefault();

    const JOB_ID = parseInt(mainForm.dataset.jobId, 10);

    const promises = pending.map(function (hrId) {
      const action = _teamQueue[hrId];
      const url    = '/recruiter/job-team/' + JOB_ID + '/' + action;
      return fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ hr_id: parseInt(hrId, 10) }),
      }).then(function (r) { return r.json(); });
    });

    Promise.all(promises)
      .then(function () {
        pending.forEach(function (id) { delete _teamQueue[id]; });
        markClean();
        mainForm.submit();
      })
      .catch(function (err) {
        console.error('Team member sync error:', err);
        showToast('Could not save team changes. Please try again.', true);
      });
  });
});


/* ═══════════════════════════════════════════════════════════
   DELETE JOB
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
  const deleteJobBtn = document.getElementById('deleteJobBtn');
  if (!deleteJobBtn) return;

  deleteJobBtn.addEventListener('click', function () {
    const appCount = parseInt(this.dataset.appCount) || 0;
    const JOB_ID   = parseInt(document.getElementById('editJobForm').dataset.jobId, 10);
    const modal    = document.getElementById('deleteJobModal');

    if (appCount > 0) {
      document.getElementById('deleteJobTitle').textContent = 'Delete Job with Active Applications';
      document.getElementById('deleteJobMessage').innerHTML =
        'This job has <strong>' + appCount + ' application(s)</strong>.'
        + ' Deleting it will permanently remove all applications. This cannot be undone.';
    } else {
      document.getElementById('deleteJobTitle').textContent   = 'Delete Job Posting';
      document.getElementById('deleteJobMessage').textContent =
        'Are you sure you want to permanently delete this job posting?';
    }

    document.getElementById('confirmDeleteJobBtn').onclick = function () {
      fetch('/recruiter/force-delete-job/' + JOB_ID, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            markClean();
            window.location.href = '/recruiter/my-job-list';
          } else {
            showToast(data.error || 'Delete failed.', true);
            closeDeleteJobModal();
          }
        })
        .catch(function () { showToast('Network error.', true); });
    };

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  });
});

function closeDeleteJobModal() {
  const modal = document.getElementById('deleteJobModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}


/* ── HTML escape helper ── */
function _esc(str) {
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}