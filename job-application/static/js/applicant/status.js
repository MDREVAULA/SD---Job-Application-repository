// ================================
// APPLICANT STATUS - JavaScript
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
        const company = row.dataset.company || '';
        const field = row.dataset.field || '';
        
        const matchesSearch = !searchTerm || 
            title.includes(searchTerm) || 
            company.includes(searchTerm) || 
            field.includes(searchTerm);
        
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
                // Sort by company A-Z
                return a.dataset.company.localeCompare(b.dataset.company);
            
            case 'z-a':
                // Sort by company Z-A
                return b.dataset.company.localeCompare(a.dataset.company);
            
            case 'status':
                // Sort by status (pending > interview > accepted > rejected)
                const statusOrder = { 'pending': 1, 'interview': 2, 'accepted': 3, 'rejected': 4 };
                const aStatus = statusOrder[a.dataset.status] || 5;
                const bStatus = statusOrder[b.dataset.status] || 5;
                return aStatus - bStatus;
            
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
                rowNumber.style.opacity = '0';
            } else {
                rowNumber.textContent = visibleIndex;
                rowNumber.style.opacity = '1';
                visibleIndex++;
            }
        }
    });
}

// ===== VIEW APPLICATION MODAL =====
function viewApplication(appId) {
    const modal = document.getElementById('applicationModal');
    const content = document.getElementById('applicationContent');
    
    // You can fetch application details via AJAX or use data attributes
    content.innerHTML = `
        <div style="padding: 10px;">
            <p><strong>Application ID:</strong> ${appId}</p>
            <p><strong>Status:</strong> Loading...</p>
            <p style="color: var(--text-secondary); font-size: 13px;">
                Fetching application details...
            </p>
        </div>
    `;
    
    modal.classList.add('active');
    
    // Optional: Fetch details via AJAX
    // fetch('/applicant/application/' + appId)
    //     .then(r => r.json())
    //     .then(data => {
    //         content.innerHTML = `...`;
    //     });
}

function closeApplicationModal() {
    document.getElementById('applicationModal').classList.remove('active');
}

// ===== VIEW REMARKS MODAL =====
function viewRemarks(appId) {
    const modal = document.getElementById('remarksModal');
    const content = document.getElementById('remarksContent');
    
    content.innerHTML = `
        <div style="padding: 10px;">
            <p><strong>Application ID:</strong> ${appId}</p>
            <p style="color: var(--text-secondary); font-size: 13px;">
                Loading recruiter remarks...
            </p>
        </div>
    `;
    
    modal.classList.add('active');
    
    // Optional: Fetch remarks via AJAX
    // fetch('/applicant/remarks/' + appId)
    //     .then(r => r.json())
    //     .then(data => {
    //         content.innerHTML = `...`;
    //     });
}

function closeRemarksModal() {
    document.getElementById('remarksModal').classList.remove('active');
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // Focus search on Ctrl+F or Cmd+F
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('jobSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // Close modals on ESC
    if (e.key === 'Escape') {
        closeApplicationModal();
        closeRemarksModal();
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

// ===== CLOSE MODAL ON OUTSIDE CLICK =====
document.addEventListener('click', function(e) {
    const appModal = document.getElementById('applicationModal');
    const remarksModal = document.getElementById('remarksModal');
    
    if (e.target === appModal) {
        closeApplicationModal();
    }
    if (e.target === remarksModal) {
        closeRemarksModal();
    }
});