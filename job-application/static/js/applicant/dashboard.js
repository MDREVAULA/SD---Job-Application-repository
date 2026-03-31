/* ============================================================
   APPLICANT DASHBOARD — Application Status JS
   Features: collapsible cards, filter by status,
             search by job title/company, sort
   ============================================================ */

let appDashCurrentSort   = 'date-desc';
let appDashCurrentStatus = 'all';

// ── Card collapse / expand ──────────────────────────────────

function appDashToggleCard(headerEl) {
    const card = headerEl.closest('.appdash-card');
    const body = card.querySelector('.appdash-card-body');
    const icon = headerEl.querySelector('.appdash-toggle-icon i');
    const isOpen = card.classList.contains('card-open');

    if (isOpen) {
        body.style.maxHeight = body.scrollHeight + 'px';
        requestAnimationFrame(() => {
            body.style.maxHeight = '0';
            body.style.opacity   = '0';
        });
        card.classList.remove('card-open');
        icon.style.transform = 'rotate(0deg)';
    } else {
        body.style.maxHeight = body.scrollHeight + 'px';
        body.style.opacity   = '1';
        card.classList.add('card-open');
        icon.style.transform = 'rotate(180deg)';

        body.addEventListener('transitionend', function onEnd() {
            if (card.classList.contains('card-open')) {
                body.style.maxHeight = 'none';
            }
            body.removeEventListener('transitionend', onEnd);
        });
    }
}

// ── Status filter tabs ──────────────────────────────────────

function appDashFilter(status) {
    appDashCurrentStatus = status;
    document.querySelectorAll('.appdash-filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-status') === status);
    });
    appDashApplyFilters();
}

// ── Search clear ────────────────────────────────────────────

function appDashClearSearch() {
    const input = document.getElementById('appDashSearch');
    if (input) input.value = '';
    const clearBtn = document.getElementById('appDashSearchClear');
    if (clearBtn) clearBtn.style.display = 'none';
    appDashApplyFilters();
}

// ── Sort ────────────────────────────────────────────────────

function appDashSetSort(sortKey) {
    appDashCurrentSort = sortKey;
    document.querySelectorAll('.appdash-sort-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-sort') === sortKey);
    });
    appDashApplyFilters();
}

// ── Core: filter + sort + render ───────────────────────────

function appDashApplyFilters() {
    const searchInput = document.getElementById('appDashSearch');
    const searchVal   = searchInput ? searchInput.value.toLowerCase().trim() : '';

    const clearBtn = document.getElementById('appDashSearchClear');
    if (clearBtn) clearBtn.style.display = searchVal ? 'flex' : 'none';

    const container = document.getElementById('appDashContainer');
    if (!container) return;

    // Remove previous no-results block
    const existing = container.querySelector('.appdash-no-results');
    if (existing) existing.remove();

    const cards = Array.from(document.querySelectorAll('.appdash-card'));

    let visibleCards = [];

    cards.forEach(card => {
        const cardStatus  = (card.getAttribute('data-status')  || '').toLowerCase();
        const cardName    = (card.getAttribute('data-name')    || '').toLowerCase();
        const cardCompany = (card.getAttribute('data-company') || '').toLowerCase();

        const statusMatch = appDashCurrentStatus === 'all' || cardStatus === appDashCurrentStatus;
        const searchMatch = !searchVal || cardName.includes(searchVal) || cardCompany.includes(searchVal);

        if (statusMatch && searchMatch) {
            card.style.display = '';
            visibleCards.push(card);
        } else {
            card.style.display = 'none';
        }
    });

    // Sort
    visibleCards.sort((a, b) => {
        if (appDashCurrentSort === 'date-desc') {
            return (b.getAttribute('data-date') || '0').localeCompare(a.getAttribute('data-date') || '0');
        } else if (appDashCurrentSort === 'date-asc') {
            return (a.getAttribute('data-date') || '0').localeCompare(b.getAttribute('data-date') || '0');
        } else if (appDashCurrentSort === 'name-asc') {
            return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
        } else if (appDashCurrentSort === 'name-desc') {
            return (b.getAttribute('data-name') || '').localeCompare(a.getAttribute('data-name') || '');
        }
        return 0;
    });

    visibleCards.forEach(card => container.appendChild(card));

    // Results count
    const resultsEl = document.getElementById('appDashResultsCount');
    if (resultsEl) {
        if (searchVal) {
            resultsEl.textContent = visibleCards.length === 0
                ? 'No results'
                : `${visibleCards.length} result${visibleCards.length !== 1 ? 's' : ''}`;
        } else {
            resultsEl.textContent = '';
        }
    }

    // Empty state
    if (visibleCards.length === 0) {
        const messages = {
            all:       { icon: 'fa-search',        title: 'No Matching Applications',   msg: 'No applications match your search.' },
            pending:   { icon: 'fa-clock',          title: 'No Pending Applications',    msg: 'You have no applications with pending status.' },
            interview: { icon: 'fa-calendar-check', title: 'No Interview Applications',  msg: 'You have no applications scheduled for interview.' },
            accepted:  { icon: 'fa-check-circle',   title: 'No Accepted Applications',   msg: 'You have no accepted applications yet.' },
            rejected:  { icon: 'fa-times-circle',   title: 'No Rejected Applications',   msg: 'You have no rejected applications.' }
        };
        const m = messages[appDashCurrentStatus] || messages.all;
        const emptyEl = document.createElement('div');
        emptyEl.className = 'appdash-no-results';
        emptyEl.innerHTML = `
            <i class="fas ${m.icon}"></i>
            <h3>${m.title}</h3>
            <p>${m.msg}</p>
        `;
        container.appendChild(emptyEl);
    }
}

// ── Tab counts ──────────────────────────────────────────────

function appDashCountTabs() {
    const cards = document.querySelectorAll('.appdash-card');
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
    appDashCountTabs();

    // Init all cards: collapsed + stagger entrance animation
    document.querySelectorAll('.appdash-card').forEach((card, index) => {
        const body = card.querySelector('.appdash-card-body');
        if (body) {
            body.style.maxHeight  = '0';
            body.style.opacity    = '0';
            body.style.overflow   = 'hidden';
            body.style.transition = 'max-height 0.35s ease, opacity 0.25s ease';
        }

        // Entrance stagger
        card.style.opacity   = '0';
        card.style.transform = 'translateY(16px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease';
            card.style.opacity    = '1';
            card.style.transform  = 'translateY(0)';
        }, 60 * index);
    });

    // Initial filter apply
    appDashApplyFilters();
});