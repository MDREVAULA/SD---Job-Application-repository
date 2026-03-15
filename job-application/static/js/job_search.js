// Job Search and Filter Functionality

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('jobSearchInput');
    const fieldFilter = document.getElementById('fieldFilter');
    const jobItems = document.querySelectorAll('.job-item');
    const jobsCountElement = document.getElementById('jobsCount');

    // Update jobs count
    function updateJobsCount() {
        const visibleJobs = Array.from(jobItems).filter(item => 
            item.style.display !== 'none'
        ).length;
        
        if (jobsCountElement) {
            jobsCountElement.textContent = visibleJobs;
        }
    }

    // Filter jobs function
    function filterJobs() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedField = fieldFilter.value.toLowerCase();

        jobItems.forEach(function(item) {
            const title = item.querySelector('.job-title-link').textContent.toLowerCase();
            const snippet = item.querySelector('.job-snippet').textContent.toLowerCase();
            const field = item.getAttribute('data-field').toLowerCase();
            const location = item.querySelector('.job-location').textContent.toLowerCase();
            const company = item.querySelector('.job-company').textContent.toLowerCase();
            
            // Check search term
            const matchesSearch = 
                title.includes(searchTerm) || 
                snippet.includes(searchTerm) ||
                location.includes(searchTerm) ||
                company.includes(searchTerm) ||
                field.includes(searchTerm);
            
            // Check field filter
            const matchesField = selectedField === '' || field === selectedField;

            // Show or hide item
            if (matchesSearch && matchesField) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });

        updateJobsCount();
    }

    // Event listeners
    if (searchInput) {
        searchInput.addEventListener('input', filterJobs);
    }

    if (fieldFilter) {
        fieldFilter.addEventListener('change', filterJobs);
    }

    // Initial count
    updateJobsCount();
});