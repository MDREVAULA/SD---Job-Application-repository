// ===================================
// JOB LIST CONTROLS - Search, Sort, Filter, View Toggle
// ===================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Get all elements
    const searchInput = document.getElementById('jobSearchInput');
    const sortSelect = document.getElementById('sortSelect');
    const viewButtons = document.querySelectorAll('.view-btn');
    const jobsContainer = document.getElementById('jobsContainer');
    const jobCards = document.querySelectorAll('.job-card-modern');

    // ===================================
    // SEARCH FUNCTIONALITY
    // ===================================
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            
            jobCards.forEach(card => {
                const title = card.getAttribute('data-title').toLowerCase();
                const field = card.getAttribute('data-field').toLowerCase();
                const location = card.getAttribute('data-location').toLowerCase();
                
                const matches = title.includes(searchTerm) || 
                               field.includes(searchTerm) || 
                               location.includes(searchTerm);
                
                if (matches) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Show empty state if no results
            checkEmptyState();
        });
    }

    // ===================================
    // SORT FUNCTIONALITY
    // ===================================
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            const cardsArray = Array.from(jobCards);
            
            cardsArray.sort((a, b) => {
                switch(sortValue) {
                    case 'a-z':
                        return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
                    
                    case 'z-a':
                        return b.getAttribute('data-title').localeCompare(a.getAttribute('data-title'));
                    
                    case 'newest':
                        const dateA = new Date(a.getAttribute('data-date') || 0);
                        const dateB = new Date(b.getAttribute('data-date') || 0);
                        return dateB - dateA;
                    
                    case 'oldest':
                        const dateA2 = new Date(a.getAttribute('data-date') || 0);
                        const dateB2 = new Date(b.getAttribute('data-date') || 0);
                        return dateA2 - dateB2;
                    
                    case 'deadline-near':
                        const deadlineA = new Date(a.getAttribute('data-deadline') || '9999-12-31');
                        const deadlineB = new Date(b.getAttribute('data-deadline') || '9999-12-31');
                        return deadlineA - deadlineB;
                    
                    case 'deadline-far':
                        const deadlineA2 = new Date(a.getAttribute('data-deadline') || '1900-01-01');
                        const deadlineB2 = new Date(b.getAttribute('data-deadline') || '1900-01-01');
                        return deadlineB2 - deadlineA2;
                    
                    case 'most-applicants':
                        const countA = parseInt(a.getAttribute('data-applicants') || 0);
                        const countB = parseInt(b.getAttribute('data-applicants') || 0);
                        return countB - countA;
                    
                    case 'least-applicants':
                        const countA2 = parseInt(a.getAttribute('data-applicants') || 0);
                        const countB2 = parseInt(b.getAttribute('data-applicants') || 0);
                        return countA2 - countB2;
                    
                    default:
                        return 0;
                }
            });
            
            // Re-append sorted cards
            cardsArray.forEach(card => {
                jobsContainer.appendChild(card);
            });
        });
    }

    // ===================================
    // VIEW TOGGLE (Grid/List)
    // ===================================
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewType = this.getAttribute('data-view');
            
            // Update active button
            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update container class
            if (jobsContainer) {
                jobsContainer.classList.remove('grid-view', 'list-view');
                jobsContainer.classList.add(viewType + '-view');
            }
        });
    });

    // ===================================
    // EMPTY STATE CHECKER
    // ===================================
    function checkEmptyState() {
        const visibleCards = Array.from(jobCards).filter(card => card.style.display !== 'none');
        
        // Remove existing empty state
        const existingEmptyState = jobsContainer.querySelector('.empty-state.search-empty');
        if (existingEmptyState) {
            existingEmptyState.remove();
        }
        
        // Show empty state if no visible cards
        if (visibleCards.length === 0 && jobCards.length > 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state search-empty';
            emptyState.innerHTML = `
                <i class="fas fa-search"></i>
                <h3>No jobs found</h3>
                <p>Try adjusting your search or filters</p>
            `;
            jobsContainer.appendChild(emptyState);
        }
    }

});