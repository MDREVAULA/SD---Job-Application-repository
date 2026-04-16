// ============================================
// Job Board — Two Column Layout
// Search, Filter, Sort Logic
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // --- Elements ---
    const searchInput       = document.getElementById('jobSearchInput');
    const categoryFilter    = document.getElementById('categoryFilter');
    const jobTypeFilter     = document.getElementById('jobTypeFilter');
    const jobsList          = document.getElementById('jobsList');
    const jobsCountEl       = document.getElementById('jobsCount');
    const sortBtn           = document.getElementById('sortBtn');
    const sortDropdown      = document.getElementById('sortDropdown');
    const sortLabel         = document.getElementById('sortLabel');
    const sortOptions       = document.querySelectorAll('.sort-option');
    const clearFiltersBtn   = document.getElementById('clearFiltersBtn');
    const resetSearchBtn    = document.getElementById('resetSearch');
    const searchEmptyState  = document.getElementById('searchEmptyState');

    // Sidebar checkboxes
    const categoryCheckboxes = document.querySelectorAll('#categoryFilters input[type="checkbox"]');
    const scheduleCheckboxes = document.querySelectorAll('#scheduleFilters input[type="checkbox"]');

    // All job items
    let allItems = Array.from(document.querySelectorAll('.job-card'));
    let currentSort = 'newest';

    // ============================================
    // GET SELECTED FILTERS FROM CHECKBOXES
    // ============================================
    function getSelectedCategories() {
        const selected = [];
        categoryCheckboxes.forEach(cb => {
            if (cb.checked) selected.push(cb.value.toLowerCase());
        });
        return selected;
    }

    function getSelectedJobTypes() {
        const selected = [];
        scheduleCheckboxes.forEach(cb => {
            if (cb.checked) selected.push(cb.value.toLowerCase());
        });
        return selected;
    }

    // ============================================
    // COUNT
    // ============================================
    function updateCount() {
        const visible = allItems.filter(item => item.style.display !== 'none').length;
        if (jobsCountEl) jobsCountEl.textContent = visible;

        if (searchEmptyState) {
            searchEmptyState.style.display = (allItems.length > 0 && visible === 0) ? 'block' : 'none';
        }
    }

    // ============================================
    // FILTER
    // ============================================
    function filterAndSort() {
        const searchTerm       = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const headerCategory   = categoryFilter ? categoryFilter.value.toLowerCase() : '';
        const headerJobType    = jobTypeFilter ? jobTypeFilter.value.toLowerCase() : '';
        
        const sidebarCategories = getSelectedCategories();
        const sidebarJobTypes   = getSelectedJobTypes();

        allItems.forEach(function (item) {
            const title    = (item.querySelector('.job-title')?.textContent || '').toLowerCase();
            const snippet  = (item.querySelector('.job-description')?.textContent || '').toLowerCase();
            const field    = (item.getAttribute('data-field') || '').toLowerCase();
            const jobType  = (item.getAttribute('data-job-type') || '').toLowerCase();
            const location = (item.querySelector('.tag-location')?.textContent || '').toLowerCase();
            const company  = (item.querySelector('.job-company')?.textContent || '').toLowerCase();

            const matchesSearch =
                !searchTerm ||
                title.includes(searchTerm) ||
                snippet.includes(searchTerm) ||
                location.includes(searchTerm) ||
                company.includes(searchTerm) ||
                field.includes(searchTerm);

            // Header filters
            const matchesHeaderCategory = !headerCategory || field === headerCategory;
            const matchesHeaderJobType  = !headerJobType  || jobType === headerJobType;

            // Sidebar filters (if any are checked, item must match at least one)
            let matchesSidebarCategory = true;
            if (sidebarCategories.length > 0) {
                matchesSidebarCategory = sidebarCategories.includes(field);
            }

            let matchesSidebarJobType = true;
            if (sidebarJobTypes.length > 0) {
                matchesSidebarJobType = sidebarJobTypes.includes(jobType);
            }

            const shouldShow = matchesSearch && 
                               matchesHeaderCategory && 
                               matchesHeaderJobType &&
                               matchesSidebarCategory &&
                               matchesSidebarJobType;

            item.style.display = shouldShow ? '' : 'none';
        });

        sortItems();
        updateCount();
    }

    // ============================================
    // SORT
    // ============================================
    function sortItems() {
        const visible = allItems.filter(item => item.style.display !== 'none');

        visible.sort(function (a, b) {
            const titleA = (a.getAttribute('data-title') || '').toLowerCase();
            const titleB = (b.getAttribute('data-title') || '').toLowerCase();
            const idA    = parseInt(a.getAttribute('data-posted') || '0', 10);
            const idB    = parseInt(b.getAttribute('data-posted') || '0', 10);

            switch (currentSort) {
                case 'newest':  return idB - idA;
                case 'oldest':  return idA - idB;
                case 'az':      return titleA.localeCompare(titleB);
                case 'za':      return titleB.localeCompare(titleA);
                default:        return 0;
            }
        });

        visible.forEach(item => jobsList.appendChild(item));
    }

    // ============================================
    // SORT DROPDOWN TOGGLE
    // ============================================
    if (sortBtn && sortDropdown) {
        sortBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = sortDropdown.classList.toggle('open');
            sortBtn.classList.toggle('open', isOpen);
        });

        document.addEventListener('click', function () {
            sortDropdown.classList.remove('open');
            sortBtn.classList.remove('open');
        });

        sortDropdown.addEventListener('click', function (e) {
            e.stopPropagation();
        });

        sortOptions.forEach(function (option) {
            option.addEventListener('click', function () {
                currentSort = this.getAttribute('data-sort');

                sortOptions.forEach(o => o.classList.remove('active'));
                this.classList.add('active');

                if (sortLabel) sortLabel.textContent = 'Sort: ' + this.textContent.trim();

                sortDropdown.classList.remove('open');
                sortBtn.classList.remove('open');

                filterAndSort();
            });
        });
    }

    // ============================================
    // CLEAR ALL FILTERS
    // ============================================
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function () {
            // Clear header filters
            if (searchInput)     searchInput.value     = '';
            if (categoryFilter)  categoryFilter.value  = '';
            if (jobTypeFilter)   jobTypeFilter.value   = '';

            // Clear sidebar checkboxes
            categoryCheckboxes.forEach(cb => cb.checked = false);
            scheduleCheckboxes.forEach(cb => cb.checked = false);

            filterAndSort();
        });
    }

    if (resetSearchBtn) {
        resetSearchBtn.addEventListener('click', function () {
            // Clear header filters
            if (searchInput)     searchInput.value     = '';
            if (categoryFilter)  categoryFilter.value  = '';
            if (jobTypeFilter)   jobTypeFilter.value   = '';

            // Clear sidebar checkboxes
            categoryCheckboxes.forEach(cb => cb.checked = false);
            scheduleCheckboxes.forEach(cb => cb.checked = false);

            filterAndSort();
        });
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================
    if (searchInput)     searchInput.addEventListener('input', filterAndSort);
    if (categoryFilter)  categoryFilter.addEventListener('change', filterAndSort);
    if (jobTypeFilter)   jobTypeFilter.addEventListener('change', filterAndSort);

    // Sidebar checkboxes
    categoryCheckboxes.forEach(cb => {
        cb.addEventListener('change', filterAndSort);
    });

    scheduleCheckboxes.forEach(cb => {
        cb.addEventListener('change', filterAndSort);
    });

    // ============================================
    // INITIAL RENDER
    // ============================================
    filterAndSort();
});
