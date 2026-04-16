// ================================
// RECRUITER JOB LIST - JavaScript
// Filter, Search, and Sort functionality
// ================================

// ===== GLOBAL STATE =====
let allJobRows = [];
let currentSort = 'newest';

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    const tbody = document.getElementById('jobTableBody');
    if (tbody) {
        allJobRows = Array.from(tbody.querySelectorAll('.job-row'));
    }
    
    // Set initial sort
    applySort();
});

// ===== SEARCH FUNCTION =====
function applySearch() {
    const searchInput = document.getElementById('jobSearchInput');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    allJobRows.forEach(row => {
        const title = row.dataset.title || '';
        const field = row.dataset.field || '';
        const location = row.dataset.location || '';
        
        const matchesSearch = !searchTerm || 
            title.includes(searchTerm) || 
            field.includes(searchTerm) || 
            location.includes(searchTerm);
        
        if (matchesSearch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update row numbers
    updateRowNumbers();
}

// ===== SORT FUNCTION =====
function applySort() {
    const sortSelect = document.getElementById('sortSelect');
    if (!sortSelect) return;
    
    currentSort = sortSelect.value;
    
    // Sort the rows
    allJobRows.sort((a, b) => {
        switch(currentSort) {
            case 'newest':
                // Sort by date descending (newest first)
                return b.dataset.date.localeCompare(a.dataset.date);
            
            case 'oldest':
                // Sort by date ascending (oldest first)
                return a.dataset.date.localeCompare(b.dataset.date);
            
            case 'a-z':
                // Sort by title A-Z
                return a.dataset.title.localeCompare(b.dataset.title);
            
            case 'z-a':
                // Sort by title Z-A
                return b.dataset.title.localeCompare(a.dataset.title);
            
            case 'deadline-near':
                // Sort by deadline ascending (nearest first)
                return a.dataset.deadline.localeCompare(b.dataset.deadline);
            
            case 'deadline-far':
                // Sort by deadline descending (farthest first)
                return b.dataset.deadline.localeCompare(a.dataset.deadline);
            
            case 'most-applicants':
                // Sort by applicants descending (most first)
                const aApplicants = parseInt(a.dataset.applicants) || 0;
                const bApplicants = parseInt(b.dataset.applicants) || 0;
                return bApplicants - aApplicants;
            
            case 'least-applicants':
                // Sort by applicants ascending (least first)
                const aApplicantsLeast = parseInt(a.dataset.applicants) || 0;
                const bApplicantsLeast = parseInt(b.dataset.applicants) || 0;
                return aApplicantsLeast - bApplicantsLeast;
            
            default:
                return 0;
        }
    });
    
    // Re-append sorted rows to table body
    const tbody = document.getElementById('jobTableBody');
    if (tbody) {
        allJobRows.forEach(row => {
            tbody.appendChild(row);
        });
    }
    
    // Update row numbers
    updateRowNumbers();
}

// ===== UPDATE ROW NUMBERS =====
function updateRowNumbers() {
    let visibleIndex = 1;
    allJobRows.forEach(row => {
        const rowNumber = row.querySelector('.row-number');
        if (rowNumber) {
            if (row.classList.contains('hidden')) {
                // Keep the original number but hide it visually
                rowNumber.style.opacity = '0';
            } else {
                rowNumber.textContent = visibleIndex;
                rowNumber.style.opacity = '1';
                visibleIndex++;
            }
        }
    });
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // Focus search on Ctrl+F or Cmd+F (prevent default browser search)
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('jobSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
});

// ===== ANIMATION ON LOAD =====
window.addEventListener('load', function() {
    const rows = document.querySelectorAll('.job-row');
    rows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 30);
    });
});
