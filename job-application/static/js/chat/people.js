// ============================================================
// people.js — Follow/Unfollow + Message restriction notices
// ============================================================

function getCsrf() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function toggleFollow(userId, btn) {
    fetch(`/chat/follow/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrf(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;

        const fc = document.getElementById(`fc-${userId}`);

        if (data.action === 'followed') {
            // Successfully followed (auto-approved)
            btn.classList.remove('btn-outline-primary', 'btn-requested');
            btn.classList.add('btn-primary', 'following');
            btn.innerHTML = '<i class="fas fa-user-check"></i> Following';
            if (fc && data.follower_count !== undefined) fc.textContent = data.follower_count;

        } else if (data.action === 'unfollowed') {
            // Unfollowed
            btn.classList.remove('btn-primary', 'following', 'btn-requested');
            btn.classList.add('btn-outline-primary');
            btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
            if (fc && data.follower_count !== undefined) fc.textContent = data.follower_count;

        } else if (data.action === 'request_sent') {
            // Follow request sent - needs approval
            btn.classList.remove('btn-outline-primary', 'btn-primary', 'following');
            btn.classList.add('btn-requested');
            btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Requested';
            // Don't update follower count for pending requests

        } else if (data.action === 'request_cancelled') {
            // Follow request cancelled
            btn.classList.remove('btn-primary', 'following', 'btn-requested');
            btn.classList.add('btn-outline-primary');
            btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
        }
    })
    .catch(err => console.error('Follow toggle error:', err));
}

// ── Message restriction toast ──
let toastTimer = null;

function showMsgRestriction(btn) {
    const card        = btn.closest('.person-card');
    const setting     = card.dataset.msgSetting;
    const displayName = card.dataset.displayName;

    let title = 'Messaging restricted';
    let text  = '';

    if (setting === 'recruiters') {
        title = 'Recruiters only';
        text  = `${displayName} only accepts messages from verified recruiters on HireBon.`;
    } else if (setting === 'mutual') {
        title = 'Mutual followers only';
        text  = `${displayName} only accepts messages from mutual followers. Follow them and wait for them to follow you back.`;
    } else {
        text = `You don't have permission to message ${displayName}.`;
    }

    const toast   = document.getElementById('msgRestrictionToast');
    const titleEl = document.getElementById('msgToastTitle');
    const textEl  = document.getElementById('msgToastText');

    if (!toast || !titleEl || !textEl) return;

    titleEl.textContent = title;
    textEl.textContent  = text;

    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(closeMsgToast, 5000);
}

function closeMsgToast() {
    const toast = document.getElementById('msgRestrictionToast');
    if (toast) toast.classList.remove('show');
}

document.addEventListener('click', (e) => {
    const toast = document.getElementById('msgRestrictionToast');
    if (toast && toast.classList.contains('show')) {
        const toastInner = toast.querySelector('.msg-toast-inner');
        if (toastInner && !toastInner.contains(e.target) && !e.target.closest('.btn-message-restricted')) {
            closeMsgToast();
        }
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMsgToast();
});