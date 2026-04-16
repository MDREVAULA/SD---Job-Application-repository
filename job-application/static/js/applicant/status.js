/* ============================================================
   APPLICANT DASHBOARD — Application Status JS
   Mirrors recruiter/applicants_filtering.js logic.
   Features: collapsible cards, filter by status,
             search by job title/company, sort
   ============================================================ */

let currentSort   = 'date-desc';
let currentStatus = 'all';

// ── Card collapse / expand ──────────────────────────────────

function toggleCard(headerEl) {
    const card = headerEl.closest('.app-card');
    const body = card.querySelector('.app-card-body');
    const isOpen = card.classList.contains('card-open');

    if (isOpen) {
        // Collapse
        body.style.maxHeight = body.scrollHeight + 'px';
        requestAnimationFrame(() => {
            body.style.maxHeight = '0';
            body.style.opacity   = '0';
        });
        card.classList.remove('card-open');
    } else {
        // Expand
        body.style.maxHeight = body.scrollHeight + 'px';
        body.style.opacity   = '1';
        card.classList.add('card-open');

        body.addEventListener('transitionend', function onEnd() {
            if (card.classList.contains('card-open')) {
                body.style.maxHeight = 'none'; // allow dynamic content
            }
            body.removeEventListener('transitionend', onEnd);
        });
    }
}

// ── Status filter tabs ──────────────────────────────────────

function filterByStatus(status) {
    currentStatus = status;
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-status') === status);
    });
    applyFilters();
}

// ── Search clear ────────────────────────────────────────────

function clearSearch() {
    const input = document.getElementById('applicantSearch');
    if (input) input.value = '';
    const clearBtn = document.getElementById('searchClear');
    if (clearBtn) clearBtn.style.display = 'none';
    applyFilters();
}

// ── Sort ────────────────────────────────────────────────────

function setSort(sortKey) {
    currentSort = sortKey;
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-sort') === sortKey);
    });
    applyFilters();
}

// ── Core: filter + sort + render ───────────────────────────

function applyFilters() {
    const searchInput = document.getElementById('applicantSearch');
    const searchVal   = searchInput ? searchInput.value.toLowerCase().trim() : '';

    // Toggle clear button
    const clearBtn = document.getElementById('searchClear');
    if (clearBtn) clearBtn.style.display = searchVal ? 'flex' : 'none';

    const container = document.getElementById('applicationsContainer');
    if (!container) return;

    // Remove previous no-results block
    const existing = container.querySelector('.no-results-state');
    if (existing) existing.remove();

    const cards = Array.from(document.querySelectorAll('.app-card'));
    let visibleCards = [];

    cards.forEach(card => {
        const cardStatus  = (card.getAttribute('data-status')  || '').toLowerCase();
        const cardName    = (card.getAttribute('data-name')    || '').toLowerCase();
        const cardCompany = (card.getAttribute('data-company') || '').toLowerCase();

        const statusMatch = currentStatus === 'all' || cardStatus === currentStatus;
        const searchMatch = !searchVal || cardName.includes(searchVal) || cardCompany.includes(searchVal);

        if (statusMatch && searchMatch) {
            card.style.display = '';
            visibleCards.push(card);
        } else {
            card.style.display = 'none';
        }
    });

    // Sort visible cards
    visibleCards.sort((a, b) => {
        if (currentSort === 'date-desc') {
            return (b.getAttribute('data-date') || '0').localeCompare(a.getAttribute('data-date') || '0');
        } else if (currentSort === 'date-asc') {
            return (a.getAttribute('data-date') || '0').localeCompare(b.getAttribute('data-date') || '0');
        } else if (currentSort === 'name-asc') {
            return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
        } else if (currentSort === 'name-desc') {
            return (b.getAttribute('data-name') || '').localeCompare(a.getAttribute('data-name') || '');
        }
        return 0;
    });

    // Re-append in sorted order
    visibleCards.forEach(card => container.appendChild(card));

    // Results count label
    const resultsEl = document.getElementById('resultsCount');
    if (resultsEl) {
        if (searchVal) {
            resultsEl.textContent = visibleCards.length === 0
                ? 'No results'
                : `${visibleCards.length} result${visibleCards.length !== 1 ? 's' : ''}`;
        } else {
            resultsEl.textContent = '';
        }
    }

    // Empty state message
    if (visibleCards.length === 0) {
        const messages = {
            all:       { icon: 'fa-search',        title: 'No Matching Applications',  msg: 'No applications match your search.' },
            pending:   { icon: 'fa-clock',          title: 'No Pending Applications',   msg: 'You have no applications with pending status.' },
            interview: { icon: 'fa-calendar-check', title: 'No Interview Scheduled',    msg: 'You have no applications scheduled for interview.' },
            accepted:  { icon: 'fa-check-circle',   title: 'No Accepted Applications',  msg: 'You have no accepted applications yet.' },
            rejected:  { icon: 'fa-times-circle',   title: 'No Rejected Applications',  msg: 'You have no rejected applications.' }
        };
        const m = messages[currentStatus] || messages.all;
        const emptyEl = document.createElement('div');
        emptyEl.className = 'no-results-state';
        emptyEl.innerHTML = `
            <i class="fas ${m.icon}"></i>
            <h3>${m.title}</h3>
            <p>${m.msg}</p>
        `;
        container.appendChild(emptyEl);
    }
}

// ── Tab counts ──────────────────────────────────────────────

function countApplications() {
    const cards = document.querySelectorAll('.app-card');
    const counts = { pending: 0, interview: 0, accepted: 0, rejected: 0 };

    cards.forEach(card => {
        const s = (card.getAttribute('data-status') || '').toLowerCase();
        if (counts.hasOwnProperty(s)) counts[s]++;
    });

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('tabPendingCount',   counts.pending);
    set('tabInterviewCount', counts.interview);
    set('tabAcceptedCount',  counts.accepted);
    set('tabRejectedCount',  counts.rejected);
}

// ── Init ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    countApplications();

    // Initialise all cards: collapsed + staggered entrance animation
    document.querySelectorAll('.app-card').forEach((card, index) => {
        const body = card.querySelector('.app-card-body');
        if (body) {
            body.style.maxHeight  = '0';
            body.style.opacity    = '0';
            body.style.overflow   = 'hidden';
            body.style.transition = 'max-height 0.35s ease, opacity 0.25s ease';
        }

        // Staggered entrance
        card.style.opacity   = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.2s, border-color 0.2s';
            card.style.opacity    = '1';
            card.style.transform  = 'translateY(0)';
        }, 80 * index);
    });

    // Run initial filter pass
    applyFilters();
});