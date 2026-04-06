// ============================================================
// people.js — Follow/Unfollow logic for People page
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