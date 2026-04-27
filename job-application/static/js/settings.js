/* ============================================================
   SETTINGS PAGE — settings.js
   ============================================================ */

const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

/* ── Section navigation ─────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {

    // Nav buttons
    document.querySelectorAll('.settings-nav-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const target = this.dataset.section;

            document.querySelectorAll('.settings-nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));

            this.classList.add('active');
            const section = document.getElementById('section-' + target);
            if (section) section.classList.add('active');
        });
    });

    /* ── Settings search ─────────────────────────────────── */
    const searchInput = document.getElementById('settingsSearch');
    const searchDrop  = document.getElementById('searchResults');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const q = this.value.trim().toLowerCase();
            searchDrop.innerHTML = '';
            if (!q) { searchDrop.classList.remove('show'); return; }

            const cards = document.querySelectorAll('[data-searchable]');
            const hits  = [];
            cards.forEach(card => {
                if (card.getAttribute('data-searchable').toLowerCase().includes(q)) {
                    const h4 = card.querySelector('h4');
                    const section = card.closest('.settings-section');
                    if (h4 && section) {
                        hits.push({ label: h4.textContent.trim(), sectionId: section.id });
                    }
                }
            });

            if (!hits.length) {
                searchDrop.innerHTML = '<div class="search-result-item" style="color:var(--text-muted)"><i class="fas fa-times-circle"></i> No results</div>';
            } else {
                hits.forEach(h => {
                    const item = document.createElement('div');
                    item.className = 'search-result-item';
                    item.innerHTML = `<i class="fas fa-angle-right"></i> ${h.label}`;
                    item.addEventListener('click', function () {
                        const sectionKey = h.sectionId.replace('section-', '');
                        const btn = document.querySelector(`.settings-nav-btn[data-section="${sectionKey}"]`);
                        if (btn) btn.click();
                        searchDrop.classList.remove('show');
                        searchInput.value = '';
                    });
                    searchDrop.appendChild(item);
                });
            }
            searchDrop.classList.add('show');
        });

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target)) searchDrop.classList.remove('show');
        });
    }

    /* ── Profile audience sub-checkboxes ─────────────────── */
    const showProfileRadios = document.querySelectorAll('input[name="show_profile"]');
    const audienceOptions   = document.getElementById('profileAudienceOptions');

    showProfileRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (audienceOptions) {
                audienceOptions.style.display = this.value === 'specific' ? 'flex' : 'none';
            }
        });
    });

    /* ── 2FA toggle — auto-save on change ────────────────── */
    const twoFactorToggle = document.querySelector('input[name="two_factor"]');
    if (twoFactorToggle) {
        twoFactorToggle.addEventListener('change', function () {
            const enabled = this.checked;

            fetch('/settings/save', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json','X-CSRFToken': CSRF_TOKEN }, 
                body:    JSON.stringify({
                    section:    'security',
                    two_factor: enabled
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showToast(enabled
                        ? '🔐 Two-factor authentication enabled.'
                        : 'Two-factor authentication disabled.'
                    );
                } else {
                    showToast(data.message || 'Could not save 2FA setting.', true);
                    // Revert the toggle on failure
                    twoFactorToggle.checked = !enabled;
                }
            })
            .catch(() => {
                showToast('Network error. Please try again.', true);
                twoFactorToggle.checked = !enabled;
            });
        });
    }

    /* ── Sync theme buttons on load ──────────────────────── */
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    _highlightThemeBtn(currentTheme);
});

/* ── Help modal helpers ─────────────────────────────────── */
function openHelp() {
    const m = document.getElementById('helpModal');
    if (m) m.style.display = 'flex';
}

function closeHelp() {
    const m = document.getElementById('helpModal');
    if (m) m.style.display = 'none';
}

function openSupportChat() {
    closeHelp();
    const m = document.getElementById('supportChatModal');
    if (m) m.style.display = 'flex';
}

function closeSupportChat() {
    const m = document.getElementById('supportChatModal');
    if (m) m.style.display = 'none';
}

/* ── FAQ accordion ──────────────────────────────────────── */
function toggleFaqCat(btn) {
    const body = btn.nextElementSibling;
    const isOpen = body.classList.toggle('open');
    btn.classList.toggle('open', isOpen);
}

function toggleFaq(btn) {
    const answer = btn.nextElementSibling;
    const isOpen = answer.classList.toggle('open');
    btn.classList.toggle('open', isOpen);
}

function filterHelp(query) {
    const q = query.trim().toLowerCase();
    document.querySelectorAll('.faq-category').forEach(cat => {
        const keywords = (cat.dataset.keywords || '').toLowerCase();
        const text     = cat.textContent.toLowerCase();
        cat.classList.toggle('hidden', q !== '' && !keywords.includes(q) && !text.includes(q));
    });
}

/* ── Support chat ───────────────────────────────────────── */
function sendChatMsg() {
    const input = document.getElementById('chatInput');
    const body  = document.getElementById('chatMessages');
    if (!input || !input.value.trim()) return;

    const msg = document.createElement('div');
    msg.className = 'chat-msg user-msg';
    msg.innerHTML = `<span>${input.value.trim()}</span><time>just now</time>`;
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
    input.value = '';

    setTimeout(() => {
        const reply = document.createElement('div');
        reply.className = 'chat-msg support-msg';
        reply.innerHTML = `<span>Thanks for reaching out! Our support team will get back to you shortly.</span><time>just now</time>`;
        body.appendChild(reply);
        body.scrollTop = body.scrollHeight;
    }, 800);
}

/* ── Toast notification ─────────────────────────────────── */
function showToast(message, isError = false) {
    const toast = document.getElementById('toastNotif');
    if (!toast) return;
    toast.textContent = message;
    toast.className   = 'toast-notif' + (isError ? ' error' : '');
    void toast.offsetWidth;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

/* ── Deactivate account ─────────────────────────────────── */
function confirmDeactivate() {
    if (!confirm('Are you sure you want to deactivate your account? You can reactivate it by logging back in.')) return;
    fetch('/settings/deactivate', { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN } })
        .then(r => r.json())
        .then(data => {
            if (data.success) window.location.href = '/login';
            else showToast('Could not deactivate. Please try again.', true);
        })
        .catch(() => showToast('An error occurred.', true));
}

/* ── Logout all devices ─────────────────────────────────── */
function confirmLogoutAll() {
    if (!confirm('Log out from all other devices?')) return;
    fetch('/settings/logout-all', { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN } })
        .then(r => r.json())
        .then(data => {
            if (data.success) showToast('Logged out from all other devices.');
            else showToast('Could not complete request.', true);
        })
        .catch(() => showToast('An error occurred.', true));
}

/* ============================================================
   THEME
   ============================================================ */
function setTheme(theme) {
    if (typeof applyUserTheme === 'function') {
        applyUserTheme(theme);
    } else {
        document.documentElement.setAttribute('data-theme', theme);
    }

    _highlightThemeBtn(theme);

    fetch('/settings/save', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json','X-CSRFToken': CSRF_TOKEN },
        body:    JSON.stringify({ section: 'appearance', theme: theme })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('Theme saved!');
        } else {
            showToast(data.message || 'Could not save theme.', true);
        }
    })
    .catch(() => showToast('Network error saving theme.', true));
}

function _highlightThemeBtn(theme) {
    document.querySelectorAll('.theme-btn').forEach(btn => {
        const onclick = btn.getAttribute('onclick') || '';
        const active  = onclick.includes("'" + theme + "'") || onclick.includes('"' + theme + '"');
        btn.classList.toggle('active', active);
    });
}

/* ============================================================
   SAVE SETTINGS — generic handler
   ============================================================ */
function saveSettings(section) {
    const payload = { section };

    if (section === 'privacy') {
        const showName = document.querySelector('input[name="show_name"]:checked');
        if (showName) payload.show_name = showName.value;

        const showProfile = document.querySelector('input[name="show_profile"]:checked');
        if (showProfile) {
            payload.show_profile = showProfile.value;
            if (showProfile.value === 'specific') {
                payload.profile_audience = Array.from(
                    document.querySelectorAll('input[name="profile_audience"]:checked')
                ).map(cb => cb.value);
            }
        }

        const showFollow = document.querySelector('input[name="show_follow_list"]:checked');
        if (showFollow) payload.show_follow_list = showFollow.value;

        const showCount = document.querySelector('input[name="show_follow_count"]:checked');
        if (showCount) payload.show_follow_count = showCount.value;

        const whoMsg = document.querySelector('input[name="who_can_message"]:checked');
        if (whoMsg) payload.who_can_message = whoMsg.value;

    } else if (section === 'notifications') {
        payload.notif_app_status = document.querySelector('input[name="notif_app_status"]')?.checked || false;
        payload.notif_messages   = document.querySelector('input[name="notif_messages"]')?.checked   || false;
        payload.notif_followers  = document.querySelector('input[name="notif_followers"]')?.checked  || false;
        payload.notif_jobs       = document.querySelector('input[name="notif_jobs"]')?.checked       || false;

    } else if (section === 'email') {
        const newEmail = document.getElementById('newEmail')?.value.trim();
        if (!newEmail) { showToast('Please enter a new email address.', true); return; }
        payload.new_email = newEmail;

    } else if (section === 'password') {
        const cur  = document.getElementById('currentPass')?.value;
        const nw   = document.getElementById('newPass')?.value;
        const conf = document.getElementById('confirmPass')?.value;
        if (!cur || !nw || !conf) { showToast('Please fill in all password fields.', true); return; }
        if (nw !== conf)          { showToast('New passwords do not match.', true); return; }
        if (nw.length < 8)        { showToast('Password must be at least 8 characters.', true); return; }
        payload.current_password = cur;
        payload.new_password     = nw;
        payload.confirm_password = conf;

    } else if (section === 'appearance') {
        const density = document.querySelector('input[name="density"]:checked');
        if (density) payload.density = density.value;

    } else if (section === 'language') {
        const lang = document.querySelector('select[name="language"]');
        const tz   = document.querySelector('select[name="timezone"]');
        if (lang) payload.language = lang.value;
        if (tz)   payload.timezone = tz.value;
    }

    const statusEl = document.getElementById(section + 'SaveStatus')
                  || document.getElementById('notifSaveStatus');

    fetch('/settings/save', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json','X-CSRFToken': CSRF_TOKEN },
        body:    JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(section.charAt(0).toUpperCase() + section.slice(1) + ' settings saved!');
            if (statusEl) {
                statusEl.textContent = '✓ Saved';
                statusEl.classList.add('visible');
                setTimeout(() => statusEl.classList.remove('visible'), 2500);
            }
        } else {
            showToast(data.message || 'Could not save settings.', true);
        }
    })
    .catch(() => showToast('Network error. Please try again.', true));
}

/* ── Unblock user ───────────────────────────────────────── */
function unblockUser(userId, username) {
    if (!confirm(`Unblock ${username}? They will be able to see your profile and message you again.`)) return;

    fetch(`/settings/unblock/${userId}`, { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN } })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const row = document.getElementById('blocked-row-' + userId);
                if (row) row.remove();

                const remaining = document.querySelectorAll('.blocked-item').length;
                const desc = document.querySelector('#section-blocked .card-desc');
                if (desc) {
                    desc.textContent = remaining > 0
                        ? `You have blocked ${remaining} user${remaining !== 1 ? 's' : ''}.`
                        : "You haven't blocked anyone.";
                }

                if (remaining === 0) {
                    const list = document.querySelector('.blocked-list');
                    if (list) {
                        list.outerHTML = `
                            <div class="blocked-empty">
                                <i class="fas fa-user-check"></i>
                                <p>Your blocked list is empty.</p>
                            </div>`;
                    }
                }

                showToast(`${username} has been unblocked.`);
            } else {
                showToast(data.message || 'Could not unblock user.', true);
            }
        })
        .catch(() => showToast('Network error. Please try again.', true));
}

document.addEventListener('DOMContentLoaded', () => {
  const s = document.getElementById('settingsSearch');
  if (s) {
    s.value = '';
    setTimeout(() => { s.value = ''; }, 50);
    setTimeout(() => { s.value = ''; }, 200);
    setTimeout(() => { s.value = ''; }, 500);
  }
});