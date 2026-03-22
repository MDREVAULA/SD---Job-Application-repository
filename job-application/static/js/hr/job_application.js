function countApplications() {
    const cards = document.querySelectorAll('.app-card');
    const counts = { pending: 0, interview: 0, accepted: 0, rejected: 0 };
    cards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (counts.hasOwnProperty(status)) counts[status]++;
    });
    document.getElementById('tabPendingCount').textContent = counts.pending;
    document.getElementById('tabInterviewCount').textContent = counts.interview;
    document.getElementById('tabAcceptedCount').textContent = counts.accepted;
    document.getElementById('tabRejectedCount').textContent = counts.rejected;
}

function filterByStatus(status) {
    const cards = document.querySelectorAll('.app-card');
    const tabs = document.querySelectorAll('.filter-tab');
    const container = document.getElementById('applicationsContainer');

    tabs.forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-status') === status);
    });

    const existingEmptyState = container.querySelector('.empty-state');
    if (existingEmptyState) existingEmptyState.remove();

    let visibleCount = 0;
    cards.forEach(card => {
        const cardStatus = card.getAttribute('data-status');
        if (status === 'all' || cardStatus === status) {
            card.style.display = 'block';
            visibleCount++;
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 10);
        } else {
            card.style.opacity = '0';
            card.style.transform = 'translateY(-10px)';
            setTimeout(() => { card.style.display = 'none'; }, 300);
        }
    });

    if (visibleCount === 0 && status !== 'all') {
        const statusMessages = {
            'pending':   { icon: 'fa-clock',         title: 'No Pending Applicants',   message: 'There are no applications with pending status at the moment.' },
            'interview': { icon: 'fa-calendar-check', title: 'No Interview Applicants', message: 'There are no applications scheduled for interview at the moment.' },
            'accepted':  { icon: 'fa-check-circle',   title: 'No Accepted Applicants',  message: 'There are no accepted applications at the moment.' },
            'rejected':  { icon: 'fa-times-circle',   title: 'No Rejected Applicants',  message: 'There are no rejected applications at the moment.' }
        };
        const m = statusMessages[status];
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `<i class="fas ${m.icon}"></i><h3>${m.title}</h3><p>${m.message}</p>`;
        container.appendChild(emptyState);
    }
}

function toggleHrDescription() {
    const wrapper = document.getElementById('hrDescriptionWrapper');
    const btn = document.getElementById('hrToggleDescBtn');
    const text = document.getElementById('hrToggleDescText');

    const isCollapsed = wrapper.classList.contains('collapsed');
    if (isCollapsed) {
        wrapper.classList.remove('collapsed');
        text.textContent = 'Show Less';
        btn.classList.add('expanded');
    } else {
        wrapper.classList.add('collapsed');
        text.textContent = 'Show More';
        btn.classList.remove('expanded');
        wrapper.closest('.job-description-full').scrollIntoView({
            behavior: 'smooth', block: 'start'
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    countApplications();

    // Description toggle init
    const wrapper = document.getElementById('hrDescriptionWrapper');
    const btn = document.getElementById('hrToggleDescBtn');
    if (wrapper && btn) {
        if (wrapper.scrollHeight > 80) {
            wrapper.classList.add('collapsed');
            btn.style.display = 'flex';
        } else {
            btn.style.display = 'none';
            const fade = document.getElementById('hrDescriptionFade');
            if (fade) fade.style.display = 'none';
        }
    }

    // Card animations
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