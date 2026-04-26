// ================================
// APPLICANT STATUS - JavaScript
// Filter, Search, and Sort functionality
// ================================

// ===== GLOBAL STATE =====
let allJobRows = [];

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function () {
    const tbody = document.getElementById('jobTableBody');
    if (tbody) {
        allJobRows = Array.from(tbody.querySelectorAll('.job-row'));
    }
    applyFilters();
});

// ===== MAIN FILTER + SORT (called by all controls) =====
function applyFilters() {
    const searchTerm  = (document.getElementById('jobSearchInput')?.value  || '').toLowerCase().trim();
    const statusVal   = (document.getElementById('statusFilter')?.value    || 'all');
    const sortVal     = (document.getElementById('sortSelect')?.value      || 'newest');

    let visible = [];

    allJobRows.forEach(row => {
        const rowStatus  = row.dataset.status  || '';
        const isRemoved  = rowStatus === 'job-removed';

        // ── Search match ──
        const title   = row.dataset.title   || '';
        const company = row.dataset.company || '';
        const field   = row.dataset.field   || '';
        const matchesSearch = !searchTerm
            || title.includes(searchTerm)
            || company.includes(searchTerm)
            || field.includes(searchTerm);

        // ── Status filter match ──
        // Job-removed rows always pass the status filter — they should
        // always be visible so the applicant knows the posting is gone,
        // regardless of what the status dropdown is set to.
        const matchesStatus = isRemoved
            || statusVal === 'all'
            || rowStatus === statusVal;

        if (matchesSearch && matchesStatus) {
            row.style.display = '';
            visible.push(row);
        } else {
            row.style.display = 'none';
        }
    });

    // ── Sort visible rows ──
    visible.sort((a, b) => {
        switch (sortVal) {
            case 'newest':
                return (b.dataset.date || '').localeCompare(a.dataset.date || '');
            case 'oldest':
                return (a.dataset.date || '').localeCompare(b.dataset.date || '');
            case 'a-z':
                return (a.dataset.company || '').localeCompare(b.dataset.company || '');
            case 'z-a':
                return (b.dataset.company || '').localeCompare(a.dataset.company || '');
            case 'status': {
                // job-removed sorts to the bottom so it doesn't dominate
                const order = { pending: 1, reviewed: 2, interviewed: 3, accepted: 4, employed: 5, rejected: 6, 'job-removed': 99 };
                return (order[a.dataset.status] || 50) - (order[b.dataset.status] || 50);
            }
            default:
                return 0;
        }
    });

    // Re-append in sorted order
    const tbody = document.getElementById('jobTableBody');
    if (tbody) {
        visible.forEach(row => tbody.appendChild(row));
    }

    // Update row numbers
    let idx = 1;
    allJobRows.forEach(row => {
        const num = row.querySelector('.row-number');
        if (!num) return;
        if (row.style.display === 'none') {
            num.textContent = '';
        } else {
            num.textContent = idx++;
        }
    });

    // Empty state
    const noResults = document.getElementById('noResults');
    if (noResults) {
        noResults.style.display = visible.length === 0 ? 'flex' : 'none';
    }
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const input = document.getElementById('jobSearchInput');
        if (input) { input.focus(); input.select(); }
    }
});

// ===== ROW ENTRANCE ANIMATION =====
window.addEventListener('load', function () {
    document.querySelectorAll('.job-row').forEach((row, i) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, i * 30);
    });
});