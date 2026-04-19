let deleteFormToSubmit = null;
let deleteJobId = null;
let deleteHasApplicants = false;

let allJobRows = [];
let currentSort = 'newest';
let currentQuery = '';

// ===== FLOATING DROPDOWN (rendered outside table) =====
let floatingMenu = null;
let activeToggleBtn = null;

function createFloatingMenu() {
    const existing = document.getElementById('floatingDropdownMenu');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.id = 'floatingDropdownMenu';
    div.style.cssText = `
        position: absolute;
        z-index: 99999;
        border-radius: 10px;
        min-width: 220px;
        padding: 6px;
        display: none;
    `;
    // Apply themed classes so CSS variables work
    div.setAttribute('data-theme', document.documentElement.getAttribute('data-theme') || 'dark');
    document.body.appendChild(div);
    return div;
}

function toggleDropdown(btn, event) {
    event.stopPropagation();
    event.preventDefault();

    const originalMenu = btn.nextElementSibling;
    if (!originalMenu) return;

    if (activeToggleBtn === btn && floatingMenu && floatingMenu.style.display === 'block') {
        closeFloatingDropdown();
        return;
    }

    if (!floatingMenu) {
        floatingMenu = createFloatingMenu();
    }

    floatingMenu.innerHTML = originalMenu.innerHTML;
    floatingMenu.style.display = 'block';
    activeToggleBtn = btn;

    positionFloatingMenu(btn);
}

function positionFloatingMenu(btn) {
    const rect = btn.getBoundingClientRect();
    const menuWidth = 220;
    const scrollY = window.scrollY || document.documentElement.scrollTop;
    const scrollX = window.scrollX || document.documentElement.scrollLeft;

    let left = rect.right - menuWidth + scrollX;
    let top = rect.bottom + 4 + scrollY;

    if (left < 8) left = 8;

    floatingMenu.style.left = left + 'px';
    floatingMenu.style.top = top + 'px';
}

function closeFloatingDropdown() {
    if (floatingMenu) floatingMenu.style.display = 'none';
    activeToggleBtn = null;
}

// Close on outside click
document.addEventListener('click', function (e) {
    if (floatingMenu && floatingMenu.style.display === 'block') {
        if (!floatingMenu.contains(e.target) && e.target !== activeToggleBtn) {
            closeFloatingDropdown();
        }
    }
});

// ===== ROW COLLECTION =====
function collectRows() {
    allJobRows = Array.from(document.querySelectorAll('tbody#jobTableBody .job-row'));
}

// ===== SEARCH =====
function applySearch() {
    currentQuery = (document.getElementById('jobSearchInput')?.value || '').toLowerCase().trim();
    applyFilters();
}

// ===== SORT =====
function applySort() {
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) currentSort = sortSelect.value;
    applyFilters();
}

// ===== FILTER + SORT =====
function applyFilters() {
    if (allJobRows.length === 0) collectRows();

    let visibleRows = [];

    allJobRows.forEach(row => {
        const title    = (row.getAttribute('data-title')    || '').toLowerCase();
        const field    = (row.getAttribute('data-field')    || '').toLowerCase();
        const location = (row.getAttribute('data-location') || '').toLowerCase();

        const matches = !currentQuery
            || title.includes(currentQuery)
            || field.includes(currentQuery)
            || location.includes(currentQuery);

        if (matches) {
            row.style.setProperty('display', '', 'important');
            visibleRows.push(row);
        } else {
            row.style.setProperty('display', 'none', 'important');
        }
    });

    const sorted = [...visibleRows].sort((a, b) => {
        switch (currentSort) {
            case 'newest':       return (b.getAttribute('data-date') || '').localeCompare(a.getAttribute('data-date') || '');
            case 'oldest':       return (a.getAttribute('data-date') || '').localeCompare(b.getAttribute('data-date') || '');
            case 'a-z':          return (a.getAttribute('data-title') || '').localeCompare(b.getAttribute('data-title') || '');
            case 'z-a':          return (b.getAttribute('data-title') || '').localeCompare(a.getAttribute('data-title') || '');
            case 'deadline-near': return (a.getAttribute('data-deadline') || '99999999999999').localeCompare(b.getAttribute('data-deadline') || '99999999999999');
            case 'deadline-far':  return (b.getAttribute('data-deadline') || '99999999999999').localeCompare(a.getAttribute('data-deadline') || '99999999999999');
            case 'most-applicants':  return (parseInt(b.getAttribute('data-applicants')) || 0) - (parseInt(a.getAttribute('data-applicants')) || 0);
            case 'least-applicants': return (parseInt(a.getAttribute('data-applicants')) || 0) - (parseInt(b.getAttribute('data-applicants')) || 0);
            default: return 0;
        }
    });

    const tbody = document.getElementById('jobTableBody');
    if (tbody) sorted.forEach(row => tbody.appendChild(row));

    updateRowNumbers();
    updateEmptyState(sorted);
}

function updateRowNumbers() {
    let visibleIndex = 1;
    allJobRows.forEach(row => {
        const rowNumber = row.querySelector('.row-number');
        if (!rowNumber) return;
        if (row.style.display === 'none') {
            rowNumber.textContent = '';
        } else {
            rowNumber.textContent = visibleIndex++;
        }
    });
}

function updateEmptyState(visibleRows) {
    let noResults = document.getElementById('noResultsRow');
    if (visibleRows.length === 0) {
        if (!noResults) {
            const tbody = document.getElementById('jobTableBody');
            if (tbody) {
                noResults = document.createElement('tr');
                noResults.id = 'noResultsRow';
                const td = document.createElement('td');
                td.colSpan = 20;
                td.style.cssText = 'text-align:center;padding:48px 24px;color:var(--text-secondary);font-size:14px;';
                td.textContent = 'No jobs match your search.';
                noResults.appendChild(td);
                tbody.appendChild(noResults);
            }
        }
    } else {
        if (noResults) noResults.remove();
    }
}

// ===== DELETE MODAL =====
function openDeleteModal(button) {
    const modal = document.getElementById('deleteModal');
    if (!modal) return;

    // Save reference BEFORE closing dropdown (closeFloatingDropdown clears activeToggleBtn)
    const savedToggleBtn = activeToggleBtn;

    closeFloatingDropdown();

    let jobId = null;
    let applicants = 0;

    // Try the saved toggle button first
    if (savedToggleBtn) {
        const row = savedToggleBtn.closest('tr');
        if (row) {
            jobId = row.dataset.jobId || null;
            applicants = parseInt(row.dataset.applicants || '0');
        }
    }

    // Fallback: try button itself (won't work for cloned floating menu, but just in case)
    if (!jobId) {
        const row = button.closest('tr');
        if (row) {
            jobId = row.dataset.jobId || null;
            applicants = parseInt(row.dataset.applicants || '0');
        }
    }

    if (!jobId) {
        console.error('Could not find job ID for deletion');
        return;
    }

    deleteJobId = jobId;
    deleteHasApplicants = applicants > 0;
    deleteFormToSubmit = null;

    const warningEl = document.getElementById('deleteWarning');
    const normalMsg  = document.getElementById('deleteNormalMsg');
    if (deleteHasApplicants) {
        if (warningEl) warningEl.style.display = 'block';
        if (normalMsg)  normalMsg.style.display = 'none';
    } else {
        if (warningEl) warningEl.style.display = 'none';
        if (normalMsg)  normalMsg.style.display = 'block';
    }

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.remove('active');
    document.body.style.overflow = '';
    deleteJobId = null;
    deleteHasApplicants = false;
}

// ===== KEYBOARD =====
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        const searchInput = document.getElementById('jobSearchInput');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    }
    if (e.key === 'Escape') {
        closeFloatingDropdown();
        closeDeleteModal();
    }
});

// ===== INIT =====
document.addEventListener('DOMContentLoaded', function () {
    floatingMenu = createFloatingMenu();

    collectRows();
    applyFilters();

    const searchInput = document.getElementById('jobSearchInput');
    if (searchInput) searchInput.addEventListener('input', applySearch);

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) sortSelect.addEventListener('change', applySort);

    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            if (!deleteJobId) return;
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Deleting…';
            try {
                const res = await fetch(`/recruiter/force-delete-job/${deleteJobId}`, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await res.json();
                if (data.success) {
                    const row = document.querySelector(`tr[data-job-id="${deleteJobId}"]`);
                    if (row) {
                        allJobRows = allJobRows.filter(r => r !== row);
                        row.remove();
                    }
                    updateRowNumbers();
                    updateEmptyState(allJobRows.filter(r => r.style.display !== 'none'));
                    closeDeleteModal();
                } else {
                    alert('Delete failed: ' + (data.error || 'Unknown error'));
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = 'Delete permanently';
                }
            } catch (err) {
                alert('Network error. Please try again.');
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Delete permanently';
            }
        });
    }

    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeDeleteModal();
        });
    }

    // Row entrance animation
    document.querySelectorAll('.job-row').forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 30);
    });
});