// ============================================
// Job Board — Search, Filter, Sort Logic
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // --- Elements ---
    const searchInput       = document.getElementById('jobSearchInput');
    const fieldFilter       = document.getElementById('fieldFilter');
    const jobTypeFilter     = document.getElementById('jobTypeFilter');
    const jobsList          = document.getElementById('jobsList');
    const jobsCountEl       = document.getElementById('jobsCount');
    const sortBtn           = document.getElementById('sortBtn');
    const sortDropdown      = document.getElementById('sortDropdown');
    const sortLabel         = document.getElementById('sortLabel');
    const sortOptions       = document.querySelectorAll('.sort-option');
    const activeFiltersBar  = document.getElementById('activeFiltersBar');
    const activeFilterTags  = document.getElementById('activeFilterTags');
    const clearAllBtn       = document.getElementById('clearAllFilters');
    const resetSearchBtn    = document.getElementById('resetSearch');
    const searchEmptyState  = document.getElementById('searchEmptyState');

    // All job items — keep original order for sorting reference
    let allItems = Array.from(document.querySelectorAll('.job-item'));
    let currentSort = 'newest';

    // ============================================
    // COUNT
    // ============================================
    function updateCount() {
        const visible = allItems.filter(item => item.style.display !== 'none').length;
        if (jobsCountEl) jobsCountEl.textContent = visible;

        // Only show "no matching" state when there ARE jobs but none match the current filter.
        // If there are no jobs at all, the server-rendered plain message is already shown.
        if (searchEmptyState) {
            searchEmptyState.style.display = (allItems.length > 0 && visible === 0) ? 'block' : 'none';
        }
    }

    // ============================================
    // FILTER
    // ============================================
    function filterAndSort() {
        const searchTerm    = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedField = fieldFilter ? fieldFilter.value.toLowerCase() : '';
        const selectedType  = jobTypeFilter ? jobTypeFilter.value.toLowerCase() : '';

        allItems.forEach(function (item) {
            const title    = (item.querySelector('.job-title-link')?.textContent || '').toLowerCase();
            const snippet  = (item.querySelector('.job-snippet')?.textContent || '').toLowerCase();
            const field    = (item.getAttribute('data-field') || '').toLowerCase();
            const jobType  = (item.getAttribute('data-job-type') || '').toLowerCase();
            const location = (item.querySelector('.location-tag')?.textContent || '').toLowerCase();
            const company  = (item.querySelector('.job-company')?.textContent || '').toLowerCase();

            const matchesSearch =
                !searchTerm ||
                title.includes(searchTerm) ||
                snippet.includes(searchTerm) ||
                location.includes(searchTerm) ||
                company.includes(searchTerm) ||
                field.includes(searchTerm);

            const matchesField = !selectedField || field === selectedField;
            const matchesType  = !selectedType  || jobType === selectedType;

            item.style.display = (matchesSearch && matchesField && matchesType) ? '' : 'none';
        });

        sortItems();
        updateActiveFilters();
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
            // data-posted stores the job ID (higher = newer in typical auto-increment DBs)
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

        // Re-append in sorted order (hidden ones stay, order is applied to all)
        visible.forEach(item => jobsList.appendChild(item));
    }

    // ============================================
    // ACTIVE FILTER TAGS
    // ============================================
    function updateActiveFilters() {
        if (!activeFilterTags) return;

        activeFilterTags.innerHTML = '';
        const tags = [];

        if (fieldFilter && fieldFilter.value) {
            tags.push({ label: fieldFilter.options[fieldFilter.selectedIndex].text, clear: () => { fieldFilter.value = ''; filterAndSort(); } });
        }
        if (jobTypeFilter && jobTypeFilter.value) {
            tags.push({ label: jobTypeFilter.options[jobTypeFilter.selectedIndex].text, clear: () => { jobTypeFilter.value = ''; filterAndSort(); } });
        }
        if (searchInput && searchInput.value.trim()) {
            tags.push({ label: `"${searchInput.value.trim()}"`, clear: () => { searchInput.value = ''; filterAndSort(); } });
        }

        tags.forEach(tag => {
            const el = document.createElement('span');
            el.className = 'filter-tag';
            el.innerHTML = `${tag.label} <button title="Remove filter"><i class="fas fa-times"></i></button>`;
            el.querySelector('button').addEventListener('click', tag.clear);
            activeFilterTags.appendChild(el);
        });

        if (activeFiltersBar) {
            activeFiltersBar.style.display = tags.length ? 'block' : 'none';
        }
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

                // Update active state
                sortOptions.forEach(o => o.classList.remove('active'));
                this.classList.add('active');

                // Update label
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
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function () {
            if (searchInput)   searchInput.value   = '';
            if (fieldFilter)   fieldFilter.value   = '';
            if (jobTypeFilter) jobTypeFilter.value = '';
            filterAndSort();
        });
    }

    if (resetSearchBtn) {
        resetSearchBtn.addEventListener('click', function () {
            if (searchInput)   searchInput.value   = '';
            if (fieldFilter)   fieldFilter.value   = '';
            if (jobTypeFilter) jobTypeFilter.value = '';
            filterAndSort();
        });
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================
    if (searchInput)   searchInput.addEventListener('input', filterAndSort);
    if (fieldFilter)   fieldFilter.addEventListener('change', filterAndSort);
    if (jobTypeFilter) jobTypeFilter.addEventListener('change', filterAndSort);

    // ============================================
    // INITIAL RENDER
    // ============================================
    filterAndSort();
});