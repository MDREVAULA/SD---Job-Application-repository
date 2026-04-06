// Count applications by status
function countApplications() {
    const cards = document.querySelectorAll('.app-card');
    const counts = {
        pending: 0,
        interview: 0,
        accepted: 0,
        rejected: 0
    };

    cards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (counts.hasOwnProperty(status)) {
            counts[status]++;
        }
    });

    // Update tab counts
    document.getElementById('tabPendingCount').textContent = counts.pending;
    document.getElementById('tabInterviewCount').textContent = counts.interview;
    document.getElementById('tabAcceptedCount').textContent = counts.accepted;
    document.getElementById('tabRejectedCount').textContent = counts.rejected;
}

// Filter applications by status
function filterByStatus(status) {
    const cards = document.querySelectorAll('.app-card');
    const tabs = document.querySelectorAll('.filter-tab');

    // Update active tab
    tabs.forEach(tab => {
        if (tab.getAttribute('data-status') === status) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Filter cards
    cards.forEach(card => {
        const cardStatus = card.getAttribute('data-status');
        if (status === 'all' || cardStatus === status) {
            card.style.display = 'block';
            // Fade in animation
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 10);
        } else {
            card.style.opacity = '0';
            card.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                card.style.display = 'none';
            }, 300);
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    countApplications();
    
    // Set initial animation state
    const cards = document.querySelectorAll('.app-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });
});