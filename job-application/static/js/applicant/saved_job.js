// ============================================
// Saved Job — Search, Filter, Sort Logic
// Mirrors job_search.js behavior
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // --- Elements ---
    const searchInput      = document.getElementById('savedSearch');
    const clearBtn         = document.getElementById('savedClear');
    const countEl          = document.getElementById('savedCount');
    const emptyEl          = document.getElementById('savedEmpty');
    const container        = document.getElementById('savedContainer');
    const fieldFilter      = document.getElementById('savedFieldFilter');
    const typeFilter       = document.getElementById('savedTypeFilter');
    const sortNewest       = document.getElementById('sortNewest');
    const sortOldest       = document.getElementById('sortOldest');
    const sortAZ           = document.getElementById('sortAZ');
    const sortZA           = document.getElementById('sortZA');
    const activeFiltersBar = document.getElementById('savedActiveFiltersBar');
    const activeFilterTags = document.getElementById('savedActiveFilterTags');
    const clearAllBtn      = document.getElementById('savedClearAll');

    let allCards   = Array.from(document.querySelectorAll('.saved-card'));
    let currentSort = 'newest';

    // ============================================
    // COUNT + EMPTY STATE
    // ============================================
    function updateCount() {
        const visible = allCards.filter(c => c.style.display !== 'none').length;
        if (countEl) countEl.textContent = visible + ' job' + (visible !== 1 ? 's' : '');
        if (emptyEl) emptyEl.style.display = (allCards.length > 0 && visible === 0) ? 'block' : 'none';
    }

    // ============================================
    // FILTER + SORT
    // ============================================
    function filterAndSort() {
        const q     = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const field = fieldFilter ? fieldFilter.value.toLowerCase() : '';
        const type  = typeFilter  ? typeFilter.value.toLowerCase()  : '';

        if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';

        allCards.forEach(function (card) {
            const title   = (card.dataset.title   || '').toLowerCase();
            const company = (card.dataset.company || '').toLowerCase();
            const cardField = (card.dataset.field || '').toLowerCase();
            const cardType  = (card.dataset.jobtype || '').toLowerCase();

            const matchSearch = !q     || title.includes(q)     || company.includes(q);
            const matchField  = !field || cardField === field;
            const matchType   = !type  || cardType  === type;

            card.style.display = (matchSearch && matchField && matchType) ? '' : 'none';
        });

        sortCards();
        updateActiveFilters();
        updateCount();
    }

    // ============================================
    // SORT
    // ============================================
    function sortCards() {
        const visible = allCards.filter(c => c.style.display !== 'none');

        visible.sort(function (a, b) {
            const titleA = (a.dataset.title || '').toLowerCase();
            const titleB = (b.dataset.title || '').toLowerCase();
            const idA    = parseInt(a.dataset.savedid || '0', 10);
            const idB    = parseInt(b.dataset.savedid || '0', 10);

            switch (currentSort) {
                case 'newest': return idB - idA;
                case 'oldest': return idA - idB;
                case 'az':     return titleA.localeCompare(titleB);
                case 'za':     return titleB.localeCompare(titleA);
                default:       return 0;
            }
        });

        visible.forEach(card => container.appendChild(card));
    }

    // ============================================
    // SORT BUTTONS
    // ============================================
    const sortBtns = document.querySelectorAll('.saved-sort-btn');

    sortBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            currentSort = this.dataset.sort;
            sortBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterAndSort();
        });
    });

    // ============================================
    // ACTIVE FILTER TAGS
    // ============================================
    function updateActiveFilters() {
        if (!activeFilterTags) return;

        activeFilterTags.innerHTML = '';
        const tags = [];

        if (fieldFilter && fieldFilter.value) {
            tags.push({
                label: fieldFilter.options[fieldFilter.selectedIndex].text,
                clear: () => { fieldFilter.value = ''; filterAndSort(); }
            });
        }
        if (typeFilter && typeFilter.value) {
            tags.push({
                label: typeFilter.options[typeFilter.selectedIndex].text,
                clear: () => { typeFilter.value = ''; filterAndSort(); }
            });
        }
        if (searchInput && searchInput.value.trim()) {
            tags.push({
                label: `"${searchInput.value.trim()}"`,
                clear: () => { searchInput.value = ''; filterAndSort(); }
            });
        }

        tags.forEach(function (tag) {
            const el = document.createElement('span');
            el.className = 'filter-tag';
            el.innerHTML = `${tag.label} <button title="Remove filter"><i class="fas fa-times"></i></button>`;
            el.querySelector('button').addEventListener('click', tag.clear);
            activeFilterTags.appendChild(el);
        });

        if (activeFiltersBar) {
            activeFiltersBar.style.display = tags.length ? 'flex' : 'none';
        }
    }

    // ============================================
    // CLEAR ALL
    // ============================================
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function () {
            if (searchInput)  searchInput.value  = '';
            if (fieldFilter)  fieldFilter.value  = '';
            if (typeFilter)   typeFilter.value   = '';
            filterAndSort();
        });
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================
    if (searchInput) searchInput.addEventListener('input', filterAndSort);
    if (clearBtn)    clearBtn.addEventListener('click',   function () { searchInput.value = ''; filterAndSort(); });
    if (fieldFilter) fieldFilter.addEventListener('change', filterAndSort);
    if (typeFilter)  typeFilter.addEventListener('change',  filterAndSort);

    // ============================================
    // INITIAL RENDER
    // ============================================
    filterAndSort();
});