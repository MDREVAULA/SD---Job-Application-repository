// ================================
// APPLICANT STATUS - JavaScript
// Search, Status Filter, and Sort
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

// ===== COMBINED FILTER + SORT =====
function applyFilters() {
    const searchTerm  = (document.getElementById('jobSearchInput')?.value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    const sortValue    = document.getElementById('sortSelect')?.value || 'newest';

    // 1. Filter
    allJobRows.forEach(row => {
        const title   = (row.dataset.title   || '').toLowerCase();
        const company = (row.dataset.company || '').toLowerCase();
        const field   = (row.dataset.field   || '').toLowerCase();
        const status  = (row.dataset.status  || '').toLowerCase();

        const matchesSearch = !searchTerm ||
            title.includes(searchTerm) ||
            company.includes(searchTerm) ||
            field.includes(searchTerm);

        const matchesStatus = statusFilter === 'all' || status === statusFilter;

        row.classList.toggle('hidden', !(matchesSearch && matchesStatus));
    });

    // 2. Sort visible rows
    const statusOrder = { 'pending': 1, 'interview': 2, 'accepted': 3, 'rejected': 4 };

    const visibleRows = allJobRows.filter(r => !r.classList.contains('hidden'));
    const hiddenRows  = allJobRows.filter(r =>  r.classList.contains('hidden'));

    visibleRows.sort((a, b) => {
        switch (sortValue) {
            case 'newest':
                return b.dataset.date.localeCompare(a.dataset.date);
            case 'oldest':
                return a.dataset.date.localeCompare(b.dataset.date);
            case 'a-z':
                return a.dataset.company.localeCompare(b.dataset.company);
            case 'z-a':
                return b.dataset.company.localeCompare(a.dataset.company);
            case 'status':
                return (statusOrder[a.dataset.status] || 5) - (statusOrder[b.dataset.status] || 5);
            default:
                return 0;
        }
    });

    // 3. Re-append (visible first, hidden after so DOM order is clean)
    const tbody = document.getElementById('jobTableBody');
    if (tbody) {
        [...visibleRows, ...hiddenRows].forEach(row => tbody.appendChild(row));
    }

    // 4. Update row numbers and no-results message
    updateRowNumbers();
    toggleNoResults(visibleRows.length === 0 && allJobRows.length > 0);
}

// Keep old function names as aliases so any inline calls still work
function applySearch() { applyFilters(); }
function applySort()   { applyFilters(); }

// ===== UPDATE ROW NUMBERS =====
function updateRowNumbers() {
    let visibleIndex = 1;
    allJobRows.forEach(row => {
        const cell = row.querySelector('.row-number');
        if (!cell) return;
        if (row.classList.contains('hidden')) {
            cell.style.opacity = '0';
        } else {
            cell.textContent   = visibleIndex++;
            cell.style.opacity = '1';
        }
    });
}

// ===== NO RESULTS MESSAGE =====
function toggleNoResults(show) {
    const el = document.getElementById('noResults');
    if (!el) return;
    el.style.display = show ? 'block' : 'none';

    // Also hide the table header when nothing visible
    const table = document.querySelector('.jobs-table');
    if (table) table.style.display = show ? 'none' : '';
}

// ===== KEYBOARD SHORTCUT: Ctrl/Cmd+F to focus search =====
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        const searchInput = document.getElementById('jobSearchInput');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    }
});

// ===== ANIMATION ON LOAD =====
window.addEventListener('load', function () {
    document.querySelectorAll('.job-row').forEach((row, index) => {
        row.style.opacity   = '0';
        row.style.transform = 'translateY(10px)';
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity    = '1';
            row.style.transform  = 'translateY(0)';
        }, index * 30);
    });
});