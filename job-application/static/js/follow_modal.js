// Shared follow modal script for own-profile pages.
// Requires window.PROFILE_USER_ID to be set before this script loads.

function refreshFollowLists(callback) {
    fetch('/profile/follow-list/' + window.PROFILE_USER_ID)
        .then(r => r.json())
        .then(data => {
            renderList('list-followers', data.followers, 'No followers yet.', 'fa-user-friends');
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
    document.getElementById('followModal').classList.remove('open');
    document.getElementById('followModalBackdrop').classList.remove('open');
    document.body.style.overflow = '';
}

function switchTab(tab) {
    activeTab = tab;
    document.getElementById('list-followers').style.display = tab === 'followers' ? 'block' : 'none';
    document.getElementById('list-following').style.display = tab === 'following' ? 'block' : 'none';
    document.getElementById('tab-followers').classList.toggle('active', tab === 'followers');
    document.getElementById('tab-following').classList.toggle('active', tab === 'following');
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeFollowModal(); });