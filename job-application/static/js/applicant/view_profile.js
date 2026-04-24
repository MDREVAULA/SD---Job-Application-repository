/* ============================================================
   APPLICANT VIEW PROFILE JS
   Merged from view_profile.js + inline scripts in view_profile.html
   ============================================================ */

const PROFILE_USER_ID = window.PROFILE_USER_ID;
const SHOW_FOLLOW_LIST = window.SHOW_FOLLOW_LIST !== undefined ? window.SHOW_FOLLOW_LIST : true;

/* ────────────────────────────────────────────────────────────
   EXPERIENCE — COLLAPSE / EXPAND (read-only, same logic as profile.js)
   ──────────────────────────────────────────────────────────── */

function toggleExpCollapse(expId) {
    const body    = document.getElementById('exp-body-' + expId);
    const chevron = document.getElementById('chevron-' + expId);
    const block   = document.getElementById('exp-block-' + expId);
    if (!body) return;
    const isOpen = !body.classList.contains('collapsed');
    if (isOpen) {
        body.classList.add('collapsed');
        chevron.classList.add('rotated');
        block.classList.add('is-collapsed');
    } else {
        body.classList.remove('collapsed');
        chevron.classList.remove('rotated');
        block.classList.remove('is-collapsed');
    }
}

/* ────────────────────────────────────────────────────────────
   CARD ENTRANCE ANIMATION
   ──────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
    /* Collapse all experience bodies by default */
    document.querySelectorAll('[id^="exp-body-"]').forEach(body => {
        body.classList.add('collapsed');
        const idNum = body.id.replace('exp-body-', '');
        const chevron = document.getElementById('chevron-' + idNum);
        const block   = document.getElementById('exp-block-' + idNum);
        if (chevron) chevron.classList.add('rotated');
        if (block)   block.classList.add('is-collapsed');
    });

    /* Stagger card entrance animation */
    document.querySelectorAll('.prof-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(12px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 80 * index);
    });
});

/* ────────────────────────────────────────────────────────────
   PRIVATE LIST NOTICE MODAL
   ──────────────────────────────────────────────────────────── */

function openPrivateListNotice() {
    const backdrop = document.getElementById('privateListBackdrop');
    const modal    = document.getElementById('privateListModal');
    if (!backdrop || !modal) return;
    backdrop.style.display = 'block';
    modal.style.display    = 'flex';
    document.body.style.overflow = 'hidden';
}

function closePrivateListNotice() {
    const backdrop = document.getElementById('privateListBackdrop');
    const modal    = document.getElementById('privateListModal');
    if (!backdrop || !modal) return;
    backdrop.style.display = 'none';
    modal.style.display    = 'none';
    document.body.style.overflow = '';
}

/* ────────────────────────────────────────────────────────────
   MESSAGE RESTRICTION NOTICE MODAL
   ──────────────────────────────────────────────────────────── */

function showPviewMsgNotice() {
    const backdrop = document.getElementById('msgRestrictBackdrop');
    const modal    = document.getElementById('msgRestrictModal');
    if (!backdrop || !modal) return;
    backdrop.style.display = 'block';
    modal.style.display    = 'flex';
    document.body.style.overflow = 'hidden';
}

function closePviewMsgNotice() {
    const backdrop = document.getElementById('msgRestrictBackdrop');
    const modal    = document.getElementById('msgRestrictModal');
    if (!backdrop || !modal) return;
    backdrop.style.display = 'none';
    modal.style.display    = 'none';
    document.body.style.overflow = '';
}

/* ────────────────────────────────────────────────────────────
   ESCAPE KEY — close all modals
   ──────────────────────────────────────────────────────────── */

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        closeFollowModal();
        closePrivateListNotice();
        closePviewMsgNotice();
    }
});

/* ────────────────────────────────────────────────────────────
   FOLLOW LIST — FETCH & RENDER
   ──────────────────────────────────────────────────────────── */

function refreshFollowLists(callback) {
    fetch('/profile/follow-list/' + PROFILE_USER_ID)
        .then(r => r.json())
        .then(data => {
            renderList('list-followers', data.followers, 'No followers yet.',         'fa-user-friends');
            renderList('list-following', data.following, 'Not following anyone yet.', 'fa-user-plus');
            document.querySelectorAll('#net-followers, #tab-count-followers').forEach(el => el.textContent = data.follower_count);
            document.querySelectorAll('#net-following, #tab-count-following').forEach(el => el.textContent = data.following_count);
            if (callback) callback(data);
        })
        .catch(err => console.error('Follow list fetch failed:', err));
}

function buildUserRow(u) {
    const avatarHtml = u.pic
        ? `<img src="${u.pic}" alt="${u.username}">`
        : `<div class="follow-modal-avatar-default">${u.username[0].toUpperCase()}</div>`;
    return `
    <a href="${u.profile_url}" class="follow-modal-item">
        <div class="follow-modal-avatar">${avatarHtml}</div>
        <div class="follow-modal-info">
            <span class="follow-modal-name">${u.username}</span>
            <span class="follow-modal-role">${u.role.charAt(0).toUpperCase() + u.role.slice(1)}</span>
        </div>
        <i class="fas fa-chevron-right follow-modal-arrow"></i>
    </a>`;
}

function renderList(listId, users, emptyMsg, emptyIcon) {
    const el = document.getElementById(listId);
    if (!el) return;
    el.innerHTML = (!users || users.length === 0)
        ? `<div class="follow-modal-empty"><i class="fas ${emptyIcon}"></i><p>${emptyMsg}</p></div>`
        : users.map(buildUserRow).join('');
}

/* ────────────────────────────────────────────────────────────
   FOLLOW / UNFOLLOW TOGGLE
   ──────────────────────────────────────────────────────────── */

function pviewToggleFollow(userId, btn) {
    fetch('/chat/follow/' + userId, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.action === 'followed') {
            btn.innerHTML = '<i class="fas fa-user-minus"></i> Unfollow';
            btn.classList.remove('prof-action-btn-primary');
            btn.classList.add('prof-action-btn-outline');
        } else {
            btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
            btn.classList.remove('prof-action-btn-outline');
            btn.classList.add('prof-action-btn-primary');
        }
        refreshFollowLists();
    })
    .catch(err => console.error('Follow toggle failed:', err));
}

/* ────────────────────────────────────────────────────────────
   FOLLOWERS / FOLLOWING MODAL
   ──────────────────────────────────────────────────────────── */

let activeTab = 'followers';

function openFollowModal(tab) {
    activeTab = tab || 'followers';
    document.getElementById('followModal').classList.add('open');
    document.getElementById('followModalBackdrop').classList.add('open');
    document.body.style.overflow = 'hidden';

    ['list-followers', 'list-following'].forEach(id => {
        document.getElementById(id).innerHTML =
            '<div class="follow-modal-empty"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div>';
    });
    refreshFollowLists(() => switchTab(activeTab));
}

function closeFollowModal() {
    const modal    = document.getElementById('followModal');
    const backdrop = document.getElementById('followModalBackdrop');
    if (modal)    modal.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    document.body.style.overflow = '';
}

function switchTab(tab) {
    activeTab = tab;
    const followersList = document.getElementById('list-followers');
    const followingList = document.getElementById('list-following');
    const tabFollowers  = document.getElementById('tab-followers');
    const tabFollowing  = document.getElementById('tab-following');

    if (followersList) followersList.style.display = tab === 'followers' ? 'block' : 'none';
    if (followingList) followingList.style.display = tab === 'following' ? 'block' : 'none';
    if (tabFollowers)  tabFollowers.classList.toggle('active', tab === 'followers');
    if (tabFollowing)  tabFollowing.classList.toggle('active', tab === 'following');
}