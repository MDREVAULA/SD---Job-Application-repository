/**
 * job_posting.js
 *
 * Handles tab switching for job-posting / edit-job pages,
 * plus syncing of hidden form fields for the new-job form.
 *
 * IMPORTANT: gallery image previews, cover-photo preview,
 * work-arrangement tags, and drag-and-drop are ALL handled
 * by job_image_preview.js — do NOT duplicate those listeners here
 * or the toggle state cancels itself on every click.
 */
document.addEventListener('DOMContentLoaded', function () {

  /* ── Tab switching (.tab-btn / .tab-content) ─────────────────── */
  document.querySelectorAll('.tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const target = btn.dataset.tab;

      document.querySelectorAll('.tab-btn')
        .forEach(function (b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-content')
        .forEach(function (c) { c.classList.remove('active'); });

      btn.classList.add('active');
      const panel = document.getElementById('tab-' + target);
      if (panel) panel.classList.add('active');
    });
  });

  /* ── Sync about_company hidden field (new-job form only) ─────── */
  const aboutTA     = document.getElementById('aboutCompanyTextarea');
  const aboutHidden = document.getElementById('aboutCompanyHidden');
  if (aboutTA && aboutHidden) {
    aboutTA.addEventListener('input', function () {
      aboutHidden.value = aboutTA.value;
    });
  }

  /* ── Sync why_join_us hidden field (new-job form only) ───────── */
  const whyTA     = document.getElementById('whyJoinUsTextarea');
  const whyHidden = document.getElementById('whyJoinUsHidden');
  if (whyTA && whyHidden) {
    whyTA.addEventListener('input', function () {
      const lines = whyTA.value
        .split('\n')
        .map(function (l) { return l.trim(); })
        .filter(Boolean);
      whyHidden.value = JSON.stringify(lines);
    });
  }

  /* ── Sidebar live-update: max_applications ───────────────────── */
  /*
   * The "Recruitment Quota" detail item in the sidebar is static HTML
   * ("Not set"). Wire up the max_applications input so the sidebar
   * reflects the typed value in real time.
   */
  const maxAppInput = document.querySelector('input[name="max_applications"]');
  if (maxAppInput) {
    // Find every sidebar quota cell across all tab sidebars
    function updateQuotaCells(val) {
      document.querySelectorAll('.detail-item').forEach(function (item) {
        const label = item.querySelector('.detail-label');
        if (label && label.textContent.trim() === 'Recruitment Quota') {
          const valueEl = item.querySelector('.detail-value');
          if (valueEl) {
            valueEl.textContent = val ? val + ' applicants max' : 'Unlimited';
          }
        }
      });
    }

    maxAppInput.addEventListener('input', function () {
      updateQuotaCells(this.value.trim());
    });

    // Reflect any pre-filled value on page load (edit mode)
    if (maxAppInput.value) {
      updateQuotaCells(maxAppInput.value.trim());
    }
  }

  /* ── Company Values editor (new-job / Hiring Team tab) ───────── */
  /*
   * The job_posting.html "Hiring Team" tab has a static values display.
   * We add an inline edit capability identical to edit_job so that
   * whatever the recruiter types gets serialised to JSON and stored
   * via the hidden <input name="company_values"> that we add below.
   *
   * The hidden input is injected here so no template change is needed
   * beyond ensuring the form reaches post_job with the field.
   */
  const hiringTeamTab = document.getElementById('tab-hiring-team');
  if (hiringTeamTab) {
    // ── Inject the hidden company_values field into the parent <form> ──
    const mainForm = document.querySelector('form[action]');
    if (mainForm && !mainForm.querySelector('input[name="company_values"]')) {
      const cvHidden = document.createElement('input');
      cvHidden.type  = 'hidden';
      cvHidden.name  = 'company_values';
      cvHidden.id    = 'companyValuesHidden';
      mainForm.appendChild(cvHidden);
    }

    // ── Wire the static Values section to be editable ──────────────
    const valuesDisplay  = hiringTeamTab.querySelector('.company-values');
    if (valuesDisplay && !document.getElementById('valuesEditSection')) {
      // Build an edit button + edit form below the existing display
      const editSection = document.createElement('div');
      editSection.id    = 'valuesEditSection';
      editSection.style.marginTop = '16px';

      editSection.innerHTML = `
        <button type="button" id="editValuesBtn" class="btn-edit-text"
          style="margin-bottom:12px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Edit Values
        </button>
        <div id="valuesEditForm" style="display:none;">
          <div id="valuesEditorList"></div>
          <button type="button" id="addValueRowBtn" class="btn-add-value"
            style="margin-top:8px;">+ Add Value</button>
          <div class="edit-actions" style="margin-top:12px;">
            <button type="button" id="saveValuesBtn"   class="btn-save-section">Save Values</button>
            <button type="button" id="cancelValuesBtn" class="btn-cancel-section">Cancel</button>
          </div>
        </div>
      `;

      // Insert right after the .company-values div's parent card header
      const card = valuesDisplay.closest('.content-card');
      if (card) card.appendChild(editSection);

      /* default seed values matching the static HTML */
      const defaultValues = [
        { title: 'Innovation',   description: 'We encourage creative thinking and embrace new ideas to drive progress.' },
        { title: 'Collaboration',description: 'Teamwork and open communication are at the heart of everything we do.' },
        { title: 'Excellence',   description: 'We strive for the highest quality in our work and continuous improvement.' },
      ];

      let currentValues = defaultValues.slice();

      function renderEditorRows(values) {
        const list = document.getElementById('valuesEditorList');
        list.innerHTML = '';
        values.forEach(function (v) {
          addValueRow(v.title, v.description);
        });
      }

      function addValueRow(title, desc) {
        title = title || '';
        desc  = desc  || '';
        const row = document.createElement('div');
        row.className = 'value-editor-row';
        row.style.cssText = 'margin-bottom:10px;';
        row.innerHTML = `
          <input type="text" class="input-text value-title-input"
            placeholder="Value title" value="${escHtmlJS(title)}"
            style="margin-bottom:6px;display:block;width:100%;">
          <input type="text" class="input-text value-desc-input"
            placeholder="Short description" value="${escHtmlJS(desc)}"
            style="display:block;width:calc(100% - 32px);display:inline-block;">
          <button type="button" class="btn-remove-value"
            onclick="this.parentElement.remove()" style="margin-left:6px;">×</button>
        `;
        document.getElementById('valuesEditorList').appendChild(row);
      }

      function escHtmlJS(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
      }

      function collectValues() {
        return Array.from(
          document.querySelectorAll('#valuesEditorList .value-editor-row')
        ).map(function (row) {
          return {
            title:       row.querySelector('.value-title-input').value.trim(),
            description: row.querySelector('.value-desc-input').value.trim(),
          };
        }).filter(function (v) { return v.title; });
      }

      function renderValuesDisplay(values) {
        valuesDisplay.innerHTML = values.map(function (v) {
          return `
            <div class="value-item">
              <div class="value-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77
                    l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <div class="value-content">
                <h5 class="value-title">${escHtmlJS(v.title)}</h5>
                <p class="value-description">${escHtmlJS(v.description)}</p>
              </div>
            </div>`;
        }).join('');
      }

      // Edit button — show form
      document.getElementById('editValuesBtn').addEventListener('click', function () {
        renderEditorRows(currentValues);
        valuesDisplay.style.display  = 'none';
        this.style.display           = 'none';
        document.getElementById('valuesEditForm').style.display = 'block';
      });

      // Add row button
      document.getElementById('addValueRowBtn').addEventListener('click', function () {
        addValueRow('', '');
      });

      // Save button
      document.getElementById('saveValuesBtn').addEventListener('click', function () {
        currentValues = collectValues();
        renderValuesDisplay(currentValues);
        // Persist to hidden field
        const hidden = document.getElementById('companyValuesHidden');
        if (hidden) hidden.value = JSON.stringify(currentValues);
        // Hide form, show display + edit button
        document.getElementById('valuesEditForm').style.display = 'none';
        document.getElementById('editValuesBtn').style.display  = '';
        valuesDisplay.style.display = '';
      });

      // Cancel button
      document.getElementById('cancelValuesBtn').addEventListener('click', function () {
        document.getElementById('valuesEditForm').style.display = 'none';
        document.getElementById('editValuesBtn').style.display  = '';
        valuesDisplay.style.display = '';
      });
    }
  }

});