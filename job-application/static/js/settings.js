/**
 * settings.js
 * Handles all interactivity for the Settings page:
 *  - Sidebar nav switching
 *  - Search bar with live results
 *  - Privacy toggles / conditional logic
 *  - Save to backend via fetch
 *  - Help Center modal (FAQ accordion, search)
 *  - Support Chat modal
 *  - Toast notifications
 */

/* ════════════════════════════════════
   1. SIDEBAR NAVIGATION
════════════════════════════════════ */
document.querySelectorAll('.settings-nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.section;

    // Update active button
    document.querySelectorAll('.settings-nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Show matching section
    document.querySelectorAll('.settings-section').forEach(sec => sec.classList.remove('active'));
    const section = document.getElementById('section-' + target);
    if (section) section.classList.add('active');
  });
});


/* ════════════════════════════════════
   2. SETTINGS SEARCH BAR
════════════════════════════════════ */
const settingsSearchInput  = document.getElementById('settingsSearch');
const searchResultsDropdown = document.getElementById('searchResults');

// Build a searchable index from all cards
function buildSearchIndex() {
  const index = [];
  document.querySelectorAll('.settings-card[data-searchable]').forEach(card => {
    const keywords = card.dataset.searchable || '';
    const heading  = card.querySelector('h4')?.textContent || '';
    const desc     = card.querySelector('.card-desc')?.textContent || '';

    // Find which section this card lives in
    const section = card.closest('.settings-section');
    const sectionId = section ? section.id.replace('section-', '') : '';

    // Find matching nav label
    const navBtn = document.querySelector(`.settings-nav-btn[data-section="${sectionId}"]`);
    const sectionLabel = navBtn ? navBtn.textContent.trim() : sectionId;

    index.push({ keywords, heading, desc, sectionId, sectionLabel, card });
  });

  // Also index individual toggle rows inside notification cards
  document.querySelectorAll('.toggle-row[data-searchable]').forEach(row => {
    const keywords = row.dataset.searchable || '';
    const heading  = row.querySelector('strong')?.textContent || '';
    const section  = row.closest('.settings-section');
    const sectionId = section ? section.id.replace('section-', '') : '';
    const navBtn = document.querySelector(`.settings-nav-btn[data-section="${sectionId}"]`);
    const sectionLabel = navBtn ? navBtn.textContent.trim() : sectionId;
    index.push({ keywords, heading, desc: '', sectionId, sectionLabel, card: row.closest('.settings-card') });
  });

  return index;
}

const searchIndex = buildSearchIndex();

settingsSearchInput.addEventListener('input', function () {
  const query = this.value.trim().toLowerCase();

  if (!query) {
    searchResultsDropdown.innerHTML = '';
    searchResultsDropdown.classList.remove('show');
    return;
  }

  const results = searchIndex.filter(item =>
    item.keywords.toLowerCase().includes(query) ||
    item.heading.toLowerCase().includes(query) ||
    item.desc.toLowerCase().includes(query)
  );

  if (results.length === 0) {
    searchResultsDropdown.innerHTML =
      `<div class="search-result-item"><i class="fas fa-exclamation-circle"></i> No results for "${query}"</div>`;
  } else {
    const seen = new Set();
    searchResultsDropdown.innerHTML = results
      .filter(r => {
        if (seen.has(r.heading)) return false;
        seen.add(r.heading);
        return true;
      })
      .slice(0, 8)
      .map(r => `
        <div class="search-result-item" data-section="${r.sectionId}">
          <i class="fas fa-arrow-right"></i>
          <span><strong>${r.heading}</strong> <small style="color:#94a3b8">· ${r.sectionLabel}</small></span>
        </div>`)
      .join('');

    // Click to navigate
    searchResultsDropdown.querySelectorAll('.search-result-item[data-section]').forEach(item => {
      item.addEventListener('click', () => {
        const sec = item.dataset.section;
        document.querySelector(`.settings-nav-btn[data-section="${sec}"]`)?.click();
        settingsSearchInput.value = '';
        searchResultsDropdown.classList.remove('show');

        // Scroll card into view after short delay
        setTimeout(() => {
          const match = searchIndex.find(r => r.sectionId === sec && r.heading === item.querySelector('strong').textContent);
          match?.card?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 120);
      });
    });
  }

  searchResultsDropdown.classList.add('show');
});

// Close dropdown when clicking outside
document.addEventListener('click', e => {
  if (!e.target.closest('.settings-search-wrap')) {
    searchResultsDropdown.classList.remove('show');
  }
});


/* ════════════════════════════════════
   3. PRIVACY — CONDITIONAL LOGIC
════════════════════════════════════ */

// Documents audience sub-options
document.querySelectorAll('input[name="show_docs"]').forEach(radio => {
  radio.addEventListener('change', function () {
    const subOptions = document.getElementById('docsSubOptions');
    if (subOptions) {
      subOptions.style.display = this.value === 'custom' ? 'flex' : 'none';
    }
  });
});

// Follow count auto-disable when follow list is hidden
const followListRadios = document.querySelectorAll('input[name="show_follow_list"]');
const followCountOptions = document.getElementById('followCountOptions');
const followCountBadge  = document.getElementById('followCountBadge');
const followCountDisabledMsg = document.getElementById('followCountDisabledMsg');

function syncFollowCountState() {
  const selectedValue = document.querySelector('input[name="show_follow_list"]:checked')?.value;
  const isHidden = selectedValue !== 'yes';

  if (followCountOptions) {
    followCountOptions.classList.toggle('follow-count-disabled', isHidden);
    followCountOptions.querySelectorAll('input').forEach(i => i.disabled = isHidden);
  }
  if (followCountBadge) followCountBadge.style.display = isHidden ? 'flex' : 'none';
  if (followCountDisabledMsg) followCountDisabledMsg.style.display = isHidden ? 'flex' : 'none';
}

followListRadios.forEach(r => r.addEventListener('change', syncFollowCountState));
// Run on page load
syncFollowCountState();


/* ════════════════════════════════════
   4. SAVE SETTINGS
════════════════════════════════════ */
async function saveSettings(section) {
  const payload = { section };

  if (section === 'privacy') {
    payload.show_name       = document.querySelector('input[name="show_name"]:checked')?.value;
    payload.show_docs       = document.querySelector('input[name="show_docs"]:checked')?.value;
    payload.docs_audience   = [...document.querySelectorAll('input[name="docs_audience"]:checked')].map(i => i.value);
    payload.show_follow_list  = document.querySelector('input[name="show_follow_list"]:checked')?.value;
    payload.show_follow_count = document.querySelector('input[name="show_follow_count"]:checked')?.value;
    payload.who_can_message   = document.querySelector('input[name="who_can_message"]:checked')?.value;
  }

  if (section === 'notifications') {
    payload.notif_app_status = document.querySelector('input[name="notif_app_status"]')?.checked;
    payload.notif_messages   = document.querySelector('input[name="notif_messages"]')?.checked;
    payload.notif_followers  = document.querySelector('input[name="notif_followers"]')?.checked;
    payload.notif_jobs       = document.querySelector('input[name="notif_jobs"]')?.checked;
  }

  if (section === 'email') {
    payload.new_email = document.getElementById('newEmail')?.value;
    if (!payload.new_email) { showToast('Please enter a new email address.', 'error'); return; }
  }

  if (section === 'password') {
    payload.current_password = document.getElementById('currentPass')?.value;
    payload.new_password     = document.getElementById('newPass')?.value;
    payload.confirm_password = document.getElementById('confirmPass')?.value;

    if (!payload.current_password || !payload.new_password) {
      showToast('Please fill in all password fields.', 'error');
      return;
    }
    if (payload.new_password !== payload.confirm_password) {
      showToast('New passwords do not match.', 'error');
      return;
    }
  }

  if (section === 'language') {
    payload.language = document.querySelector('select[name="language"]')?.value;
    payload.timezone = document.querySelector('select[name="timezone"]')?.value;
  }

  try {
    const res = await fetch('/settings/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.success) {
      showToast('✓ Settings saved successfully!');
      // Show inline save status for privacy/notifications
      const statusEl = document.getElementById(section + 'SaveStatus') || document.getElementById('privacySaveStatus');
      if (statusEl) {
        statusEl.textContent = '✓ Saved';
        statusEl.classList.add('visible');
        setTimeout(() => statusEl.classList.remove('visible'), 3000);
      }
    } else {
      showToast(data.message || 'Failed to save settings.', 'error');
    }
  } catch (err) {
    showToast('Network error. Please try again.', 'error');
    console.error(err);
  }
}


/* ════════════════════════════════════
   5. THEME SWITCHER
════════════════════════════════════ */
function setTheme(theme) {
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.theme-btn[onclick*="${theme}"]`)?.classList.add('active');
  showToast(`Theme set to ${theme}`);
  // Persist
  fetch('/settings/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ section: 'appearance', theme })
  });
}


/* ════════════════════════════════════
   6. CONFIRM DIALOGS
════════════════════════════════════ */
function confirmDeactivate() {
  if (confirm('Are you sure you want to deactivate your account? You can reactivate at any time by logging in.')) {
    fetch('/settings/deactivate', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.success) window.location.href = '/login';
        else showToast('Unable to deactivate account.', 'error');
      });
  }
}

function confirmLogoutAll() {
  if (confirm('Log out from all other devices?')) {
    fetch('/settings/logout-all', { method: 'POST' })
      .then(r => r.json())
      .then(d => showToast(d.success ? '✓ All other sessions ended.' : 'Error.'));
  }
}


/* ════════════════════════════════════
   7. HELP CENTER MODAL
════════════════════════════════════ */
const helpModal = document.getElementById('helpModal');

document.getElementById('openHelpBtn')?.addEventListener('click', () => {
  helpModal.style.display = 'flex';
  document.getElementById('helpSearch').focus();
});

function closeHelp() {
  helpModal.style.display = 'none';
}

// Close on overlay click
helpModal?.addEventListener('click', e => {
  if (e.target === helpModal) closeHelp();
});

// FAQ category toggle
function toggleFaqCat(btn) {
  const body = btn.nextElementSibling;
  const isOpen = body.classList.contains('open');

  // Close all
  document.querySelectorAll('.faq-cat-body').forEach(b => b.classList.remove('open'));
  document.querySelectorAll('.faq-cat-btn').forEach(b => b.classList.remove('open'));

  // Open clicked if it was closed
  if (!isOpen) {
    body.classList.add('open');
    btn.classList.add('open');
  }
}

// FAQ item toggle
function toggleFaq(btn) {
  const answer = btn.nextElementSibling;
  const isOpen = answer.classList.contains('open');

  // Close all in this category
  btn.closest('.faq-cat-body').querySelectorAll('.faq-a').forEach(a => a.classList.remove('open'));
  btn.closest('.faq-cat-body').querySelectorAll('.faq-q').forEach(q => q.classList.remove('open'));

  if (!isOpen) {
    answer.classList.add('open');
    btn.classList.add('open');
  }
}

// Help search filter
function filterHelp(query) {
  query = query.trim().toLowerCase();
  document.querySelectorAll('.faq-category').forEach(cat => {
    if (!query) { cat.classList.remove('hidden'); return; }
    const text = (cat.dataset.keywords + ' ' + cat.textContent).toLowerCase();
    cat.classList.toggle('hidden', !text.includes(query));
  });
}


/* ════════════════════════════════════
   8. SUPPORT CHAT MODAL
════════════════════════════════════ */
const supportChatModal = document.getElementById('supportChatModal');
const chatMessages = document.getElementById('chatMessages');
const chatInput    = document.getElementById('chatInput');

function openSupportChat() {
  closeHelp();
  supportChatModal.style.display = 'flex';
  setTimeout(() => chatInput?.focus(), 100);
}

function closeSupportChat() {
  supportChatModal.style.display = 'none';
}

supportChatModal?.addEventListener('click', e => {
  if (e.target === supportChatModal) closeSupportChat();
});

function sendChatMsg() {
  const text = chatInput?.value?.trim();
  if (!text) return;

  // Add user message
  appendChatMsg(text, 'user');
  chatInput.value = '';

  // Simulate support response
  setTimeout(() => {
    appendChatMsg("Thanks for reaching out! Our support team will get back to you shortly. In the meantime, you can browse our Help Center articles.", 'support');
  }, 900);
}

function appendChatMsg(text, sender) {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const div = document.createElement('div');
  div.className = `chat-msg ${sender === 'user' ? 'user-msg' : 'support-msg'}`;
  div.innerHTML = `<span>${escapeHtml(text)}</span><time>${now}</time>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}


/* ════════════════════════════════════
   9. TOAST NOTIFICATIONS
════════════════════════════════════ */
let toastTimer;

function showToast(message, type = 'success') {
  const toast = document.getElementById('toastNotif');
  if (!toast) return;

  toast.textContent = message;
  toast.style.background = type === 'error' ? '#dc2626' : '#1e293b';
  toast.classList.add('show');

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3200);
}