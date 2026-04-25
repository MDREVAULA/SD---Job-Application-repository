// Shared follow modal script for own-profile pages.
// Requires window.PROFILE_USER_ID to be set before this script loads.

function refreshFollowLists(callback) {
    const userId = window.PROFILE_USER_ID;
    if (!userId) {
        console.error('PROFILE_USER_ID not set');
        return;
    }
    
    fetch('/profile/follow-list/' + userId)
        .then(r => r.json())
        .then(data => {
            if (data.list_is_private) {
                renderList('list-followers', [], 'Followers list is private', 'fa-lock');
                renderList('list-following', [], 'Following list is private', 'fa-lock');
            } else {
                renderList('list-followers', data.followers, 'No followers yet.', 'fa-user-friends');
                renderList('list-following', data.following, 'Not following anyone yet.', 'fa-user-plus');
            }
            
            // Update counts if they exist in the response
            if (data.follower_count !== undefined) {
                document.querySelectorAll('#net-followers, #tab-count-followers').forEach(el => {
                    if (el) el.textContent = data.follower_count;
                });
            }
            if (data.following_count !== undefined) {
                document.querySelectorAll('#net-following, #tab-count-following').forEach(el => {
                    if (el) el.textContent = data.following_count;
                });
            }
            
            if (callback) callback(data);
        })
        .catch(err => {
            console.error('Follow list fetch failed:', err);
            renderList('list-followers', [], 'Error loading followers', 'fa-exclamation-triangle');
            renderList('list-following', [], 'Error loading following', 'fa-exclamation-triangle');
        });
}

function buildUserRow(u) {
    if (!u) return '';
    
    const avatarHtml = u.pic
        ? `<img src="${u.pic}" alt="${u.username}">`
        : `<div class="follow-modal-avatar-default">${(u.username || '?')[0].toUpperCase()}</div>`;
    
    return `
    <a href="${u.profile_url || '/profile/' + u.id}" class="follow-modal-item">
        <div class="follow-modal-avatar">${avatarHtml}</div>
        <div class="follow-modal-info">
            <span class="follow-modal-name">${escapeHtml(u.username || 'User')}</span>
            <span class="follow-modal-role">${u.role ? (u.role.charAt(0).toUpperCase() + u.role.slice(1)) : 'User'}</span>
        </div>
        <i class="fas fa-chevron-right follow-modal-arrow"></i>
    </a>`;
}

// Simple escape function to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderList(listId, users, emptyMsg, emptyIcon) {
    const el = document.getElementById(listId);
    if (!el) return;
    
    if (!users || users.length === 0) {
        el.innerHTML = `<div class="follow-modal-empty"><i class="fas ${emptyIcon}"></i><p>${escapeHtml(emptyMsg)}</p></div>`;
    } else {
        el.innerHTML = users.map(buildUserRow).join('');
    }
}

let activeTab = 'followers';
let isModalOpen = false;

function openFollowModal(tab) {
    activeTab = tab || 'followers';
    
    const modal = document.getElementById('followModal');
    const backdrop = document.getElementById('followModalBackdrop');
    
    if (!modal || !backdrop) return;
    
    // Show loading state
    ['list-followers', 'list-following'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = '<div class="follow-modal-empty"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div>';
        }
    });
    
    // Open modal
    modal.classList.add('open');
    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
    isModalOpen = true;
    
    // Load data
    refreshFollowLists(() => {
        switchTab(activeTab);
    });
}

function closeFollowModal() {
    const modal = document.getElementById('followModal');
    const backdrop = document.getElementById('followModalBackdrop');
    
    if (modal) modal.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    document.body.style.overflow = '';
    isModalOpen = false;
}

function switchTab(tab) {
    activeTab = tab;
    
    const followersList = document.getElementById('list-followers');
    const followingList = document.getElementById('list-following');
    const followersTab = document.getElementById('tab-followers');
    const followingTab = document.getElementById('tab-following');
    
    if (followersList) followersList.style.display = tab === 'followers' ? 'block' : 'none';
    if (followingList) followingList.style.display = tab === 'following' ? 'block' : 'none';
    if (followersTab) followersTab.classList.toggle('active', tab === 'followers');
    if (followingTab) followingTab.classList.toggle('active', tab === 'following');
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isModalOpen) {
        closeFollowModal();
    }
});

// Close modal when clicking on backdrop (handled by onclick in HTML, but add as backup)
document.addEventListener('click', function(e) {
    const backdrop = document.getElementById('followModalBackdrop');
    if (e.target === backdrop && isModalOpen) {
        closeFollowModal();
    }
});