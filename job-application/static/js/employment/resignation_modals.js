(function () {
  function injectModals() {
    const html = `
    <!-- ===== MODAL BACKDROP ===== -->
    <div id="resign-modal-backdrop" class="resign-modal-backdrop" aria-hidden="true"></div>

    <!-- ===== APPROVE MODAL ===== -->
    <div id="modal-approve" class="resign-modal" role="dialog" aria-modal="true" aria-labelledby="modal-approve-title">
      <div class="resign-modal-inner">
        <div class="resign-modal-icon-wrap resign-icon-approve">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <h2 class="resign-modal-title" id="modal-approve-title">Approve Resignation?</h2>
        <p class="resign-modal-desc">
          The employee will enter their <strong>rendering period</strong> and their employment
          will be officially concluded on their intended last day.
        </p>
        <p class="resign-modal-subdesc">
          This action cannot be undone. The employee will be notified immediately.
        </p>
        <div class="resign-modal-actions">
          <button class="resign-btn resign-btn-ghost" data-dismiss>Cancel</button>
          <button class="resign-btn resign-btn-approve" id="modal-approve-confirm">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Yes, Approve
          </button>
        </div>
      </div>
    </div>

    <!-- ===== REQUEST REVISION MODAL ===== -->
    <div id="modal-revision" class="resign-modal" role="dialog" aria-modal="true" aria-labelledby="modal-revision-title">
      <div class="resign-modal-inner">
        <div class="resign-modal-icon-wrap resign-icon-revision">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </div>
        <h2 class="resign-modal-title" id="modal-revision-title">Request a Revision?</h2>
        <p class="resign-modal-desc">
          The employee will be notified and asked to update their resignation with your
          note below. Make sure your note clearly explains what needs to be revised.
        </p>
        <div class="resign-modal-note-preview" id="revision-note-preview"></div>
        <div class="resign-modal-actions">
          <button class="resign-btn resign-btn-ghost" data-dismiss>Cancel</button>
          <button class="resign-btn resign-btn-revision" id="modal-revision-confirm">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Send Revision Request
          </button>
        </div>
      </div>
    </div>

    <!-- ===== REJECT MODAL ===== -->
    <div id="modal-reject" class="resign-modal" role="dialog" aria-modal="true" aria-labelledby="modal-reject-title">
      <div class="resign-modal-inner">
        <div class="resign-modal-icon-wrap resign-icon-reject">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2 class="resign-modal-title" id="modal-reject-title">Reject Resignation?</h2>
        <p class="resign-modal-desc">
          This resignation will be <strong>rejected</strong>. The employee will remain active
          and will be notified of the decision along with your reason below.
        </p>
        <div class="resign-modal-note-preview" id="reject-note-preview"></div>
        <div class="resign-modal-actions">
          <button class="resign-btn resign-btn-ghost" data-dismiss>Cancel</button>
          <button class="resign-btn resign-btn-reject" id="modal-reject-confirm">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            Yes, Reject
          </button>
        </div>
      </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
  }

  /* ── Helpers ── */
  function openModal(id) {
    document.getElementById('resign-modal-backdrop').removeAttribute('aria-hidden');
    document.getElementById('resign-modal-backdrop').classList.add('is-open');
    document.getElementById(id).classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeAll() {
    document.querySelectorAll('.resign-modal.is-open').forEach(m => m.classList.remove('is-open'));
    const backdrop = document.getElementById('resign-modal-backdrop');
    backdrop.classList.remove('is-open');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  /* ── Main confirmation function (replaces the old confirmAction) ── */
  window.confirmAction = function (type) {
    const note = document.getElementById('reviewer_note_field').value.trim();

    if (type === 'approve') {
      openModal('modal-approve');
      return false; // block native form submit; modal confirm button handles it
    }

    if (type === 'revision') {
      if (!note) {
        // Show inline error instead of alert — gracefully fall back
        shakeTextarea();
        showTextareaError('Please add a note explaining what needs to be revised.');
        return false;
      }
      document.getElementById('revision-note-preview').textContent = note;
      openModal('modal-revision');
      return false;
    }

    if (type === 'reject') {
      if (!note) {
        shakeTextarea();
        showTextareaError('Please provide a reason for rejecting this resignation.');
        return false;
      }
      document.getElementById('reject-note-preview').textContent = note;
      openModal('modal-reject');
      return false;
    }

    return false;
  };

  function shakeTextarea() {
    const ta = document.getElementById('reviewer_note_field');
    ta.classList.remove('resign-ta-shake');
    void ta.offsetWidth; // reflow to restart animation
    ta.classList.add('resign-ta-shake');
    ta.focus();
  }

  function showTextareaError(msg) {
    let err = document.getElementById('resign-ta-error');
    if (!err) {
      err = document.createElement('p');
      err.id = 'resign-ta-error';
      err.className = 'resign-ta-error';
      document.getElementById('reviewer_note_field').insertAdjacentElement('afterend', err);
    }
    err.textContent = msg;
    err.style.display = 'block';
    setTimeout(() => { err.style.display = 'none'; }, 4000);
  }

  /* ── Wire up confirm buttons inside modals ── */
  function bindModalConfirms() {
    // Approve confirm
    document.getElementById('modal-approve-confirm').addEventListener('click', function () {
      const note = document.getElementById('reviewer_note_field').value.trim();
      document.getElementById('note-approve').value = note;
      closeAll();
      document.getElementById('form-approve').submit();
    });

    // Revision confirm
    document.getElementById('modal-revision-confirm').addEventListener('click', function () {
      const note = document.getElementById('reviewer_note_field').value.trim();
      document.getElementById('note-revision').value = note;
      closeAll();
      document.getElementById('form-revision').submit();
    });

    // Reject confirm
    document.getElementById('modal-reject-confirm').addEventListener('click', function () {
      const note = document.getElementById('reviewer_note_field').value.trim();
      document.getElementById('note-reject').value = note;
      closeAll();
      document.getElementById('form-reject').submit();
    });

    // Dismiss buttons & backdrop
    document.querySelectorAll('[data-dismiss]').forEach(btn =>
      btn.addEventListener('click', closeAll)
    );
    document.getElementById('resign-modal-backdrop').addEventListener('click', closeAll);

    // Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeAll();
    });
  }

  /* ── Bootstrap ── */
  document.addEventListener('DOMContentLoaded', function () {
    injectModals();
    bindModalConfirms();
  });
})();