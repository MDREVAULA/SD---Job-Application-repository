// ===================================
// JOB LIST CONTROLS - Search, Sort, Filter, View Toggle
// ===================================

document.addEventListener('DOMContentLoaded', function () {

    const searchInput   = document.getElementById('jobSearchInput');
    const sortSelect    = document.getElementById('sortSelect');
    const viewButtons   = document.querySelectorAll('.jl-view-btn');
    const jobsContainer = document.getElementById('jobsContainer');
    const jobCards      = document.querySelectorAll('.jl-card');

    // ===================================
    // SEARCH
    // ===================================
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase().trim();

            jobCards.forEach(card => {
                const title    = (card.getAttribute('data-title')    || '').toLowerCase();
                const field    = (card.getAttribute('data-field')    || '').toLowerCase();
                const location = (card.getAttribute('data-location') || '').toLowerCase();

                const matches = title.includes(searchTerm) ||
                                field.includes(searchTerm) ||
                                location.includes(searchTerm);

                card.style.display = matches ? '' : 'none';
            });

            checkEmptyState();
        });
    }

    // ===================================
    // SORT
    // ===================================
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            const sortValue  = this.value;
            const cardsArray = Array.from(jobCards);

            cardsArray.sort((a, b) => {
                switch (sortValue) {
                    case 'a-z':
                        return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
                    case 'z-a':
                        return b.getAttribute('data-title').localeCompare(a.getAttribute('data-title'));
                    case 'newest': {
                        const dA = new Date(a.getAttribute('data-date') || 0);
                        const dB = new Date(b.getAttribute('data-date') || 0);
                        return dB - dA;
                    }
                    case 'oldest': {
                        const dA = new Date(a.getAttribute('data-date') || 0);
                        const dB = new Date(b.getAttribute('data-date') || 0);
                        return dA - dB;
                    }
                    case 'deadline-near': {
                        const dA = new Date(a.getAttribute('data-deadline') || '9999-12-31');
                        const dB = new Date(b.getAttribute('data-deadline') || '9999-12-31');
                        return dA - dB;
                    }
                    case 'deadline-far': {
                        const dA = new Date(a.getAttribute('data-deadline') || '1900-01-01');
                        const dB = new Date(b.getAttribute('data-deadline') || '1900-01-01');
                        return dB - dA;
                    }
                    case 'most-applicants': {
                        const cA = parseInt(a.getAttribute('data-applicants') || 0);
                        const cB = parseInt(b.getAttribute('data-applicants') || 0);
                        return cB - cA;
                    }
                    case 'least-applicants': {
                        const cA = parseInt(a.getAttribute('data-applicants') || 0);
                        const cB = parseInt(b.getAttribute('data-applicants') || 0);
                        return cA - cB;
                    }
                    default:
                        return 0;
                }
            });

            cardsArray.forEach(card => jobsContainer.appendChild(card));
        });
    }

    // ===================================
    // VIEW TOGGLE (Grid / List)
    // ===================================
    viewButtons.forEach(button => {
        button.addEventListener('click', function () {
            const viewType = this.getAttribute('data-view');

            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            if (jobsContainer) {
                jobsContainer.classList.remove('grid-view', 'list-view');
                jobsContainer.classList.add(viewType + '-view');
            }
        });
    });

    // ===================================
    // EMPTY STATE
    // ===================================
    function checkEmptyState() {
        const visibleCards = Array.from(jobCards).filter(c => c.style.display !== 'none');

        const existing = jobsContainer.querySelector('.jl-empty.search-empty');
        if (existing) existing.remove();

        if (visibleCards.length === 0 && jobCards.length > 0) {
            const el = document.createElement('div');
            el.className = 'jl-empty search-empty';
            el.innerHTML = `
                <i class="fas fa-search"></i>
                <h3>No jobs found</h3>
                <p>Try adjusting your search or filters</p>
            `;
            jobsContainer.appendChild(el);
        }
    }
});

// ===================================
// KEBAB MENU
// ===================================
function toggleKebab(btn) {
    const menu   = btn.nextElementSibling;
    const isOpen = menu.classList.contains('open');

    // Close all open menus first
    document.querySelectorAll('.jl-kebab-menu.open').forEach(m => m.classList.remove('open'));
    document.querySelectorAll('.jl-kebab-btn.active').forEach(b => b.classList.remove('active'));

    if (!isOpen) {
        menu.classList.add('open');
        btn.classList.add('active');
    }
}

// Close kebab when clicking outside
document.addEventListener('click', function (e) {
    if (!e.target.closest('.jl-kebab-wrap')) {
        document.querySelectorAll('.jl-kebab-menu.open').forEach(m => m.classList.remove('open'));
        document.querySelectorAll('.jl-kebab-btn.active').forEach(b => b.classList.remove('active'));
    }
});