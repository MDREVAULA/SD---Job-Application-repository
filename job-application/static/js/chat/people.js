// ============================================================
// people.js — Follow/Unfollow + Message restriction notices
// ============================================================

function toggleFollow(userId, btn) {
    fetch(`/chat/follow/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;

        const isNowFollowing = data.action === "followed";
        btn.classList.toggle("following", isNowFollowing);
        btn.innerHTML = isNowFollowing
            ? '<i class="fas fa-user-check"></i> Following'
            : '<i class="fas fa-user-plus"></i> Follow';

        // Update follower count
        const fc = document.getElementById(`fc-${userId}`);
        if (fc) fc.textContent = data.follower_count;
    });
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

    const toast    = document.getElementById('msgRestrictionToast');
    const titleEl  = document.getElementById('msgToastTitle');
    const textEl   = document.getElementById('msgToastText');

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

// Close toast on outside click
document.addEventListener('click', (e) => {
    const toast = document.getElementById('msgRestrictionToast');
    if (toast && !toast.contains(e.target)) {
        closeMsgToast();
    }
});