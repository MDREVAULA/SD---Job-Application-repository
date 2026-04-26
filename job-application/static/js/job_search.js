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

    // Availability checkboxes
    const filterActive      = document.getElementById('filterActive');
    const filterExpired     = document.getElementById('filterExpired');

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
    // Counts only VISIBLE active jobs so the number
    // reflects what the user actually sees on screen.
    // ============================================
    function updateCount() {
        const visibleActiveCount = allItems.filter(item =>
            item.style.display !== 'none' &&
            (item.getAttribute('data-status') || 'active') === 'active'
        ).length;

        if (jobsCountEl) jobsCountEl.textContent = visibleActiveCount;

        const visibleCount = allItems.filter(item => item.style.display !== 'none').length;
        if (searchEmptyState) {
            searchEmptyState.style.display =
                (allItems.length > 0 && visibleCount === 0) ? 'flex' : 'none';
        }
    }

    // ============================================
    // FILTER
    // ============================================
    function filterAndSort() {
        const searchTerm        = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const headerCategory    = categoryFilter ? categoryFilter.value.toLowerCase() : '';
        const headerJobType     = jobTypeFilter  ? jobTypeFilter.value.toLowerCase()  : '';

        const sidebarCategories = getSelectedCategories();
        const sidebarJobTypes   = getSelectedJobTypes();

        const showActive  = filterActive  ? filterActive.checked  : true;
        const showExpired = filterExpired ? filterExpired.checked : false;

        allItems.forEach(function (item) {
            const status    = (item.getAttribute('data-status') || 'active').trim();
            const isActive  = status === 'active';
            const isExpired = status === 'expired' || status === 'closed';

            // ── Availability gate ──────────────────────────────────────────
            // Hide active jobs when "Active jobs" is unchecked
            if (isActive && !showActive) {
                item.style.display = 'none';
                return;
            }
            // Hide expired/closed jobs when "Show closed & expired" is unchecked
            if (isExpired && !showExpired) {
                item.style.display = 'none';
                return;
            }
            // Hide anything that is neither active nor expired (safety fallback)
            if (!isActive && !isExpired) {
                item.style.display = 'none';
                return;
            }

            // ── Text / field data ──────────────────────────────────────────
            const title    = (item.querySelector('.job-title')?.textContent  || '').toLowerCase();
            const snippet  = (item.querySelector('.job-description')?.textContent || '').toLowerCase();
            const field    = (item.getAttribute('data-field')    || '').toLowerCase();
            const jobType  = (item.getAttribute('data-job-type') || '').toLowerCase();
            const location = (item.querySelector('.tag-location')?.textContent || '').toLowerCase();
            const company  = (item.querySelector('.job-company')?.textContent  || '').toLowerCase();

            const matchesSearch =
                !searchTerm ||
                title.includes(searchTerm)    ||
                snippet.includes(searchTerm)  ||
                location.includes(searchTerm) ||
                company.includes(searchTerm)  ||
                field.includes(searchTerm);

            // Header filters
            const matchesHeaderCategory = !headerCategory || field   === headerCategory;
            const matchesHeaderJobType  = !headerJobType  || jobType === headerJobType;

            // Sidebar filters — if any checked, item must match at least one
            let matchesSidebarCategory = true;
            if (sidebarCategories.length > 0) {
                matchesSidebarCategory = sidebarCategories.includes(field);
            }

            let matchesSidebarJobType = true;
            if (sidebarJobTypes.length > 0) {
                matchesSidebarJobType = sidebarJobTypes.includes(jobType);
            }

            const shouldShow =
                matchesSearch          &&
                matchesHeaderCategory  &&
                matchesHeaderJobType   &&
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
                case 'newest': return idB - idA;
                case 'oldest': return idA - idB;
                case 'az':     return titleA.localeCompare(titleB);
                case 'za':     return titleB.localeCompare(titleA);
                default:       return 0;
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
    function clearAll() {
        if (searchInput)    searchInput.value    = '';
        if (categoryFilter) categoryFilter.value = '';
        if (jobTypeFilter)  jobTypeFilter.value  = '';

        // Reset sidebar checkboxes
        categoryCheckboxes.forEach(cb => cb.checked = false);
        scheduleCheckboxes.forEach(cb => cb.checked = false);

        // Reset availability to defaults: Active ON, Expired OFF
        if (filterActive)  filterActive.checked  = true;
        if (filterExpired) filterExpired.checked = false;

        filterAndSort();
    }

    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearAll);
    if (resetSearchBtn)  resetSearchBtn.addEventListener('click',  clearAll);

    // ============================================
    // EVENT LISTENERS
    // ============================================
    if (searchInput)    searchInput.addEventListener('input',    filterAndSort);
    if (categoryFilter) categoryFilter.addEventListener('change', filterAndSort);
    if (jobTypeFilter)  jobTypeFilter.addEventListener('change',  filterAndSort);

    // Availability
    if (filterActive)  filterActive.addEventListener('change',  filterAndSort);
    if (filterExpired) filterExpired.addEventListener('change', filterAndSort);

    // Sidebar checkboxes
    categoryCheckboxes.forEach(cb => cb.addEventListener('change', filterAndSort));
    scheduleCheckboxes.forEach(cb => cb.addEventListener('change', filterAndSort));

    // ============================================
    // INITIAL RENDER
    // ============================================
    filterAndSort();
});