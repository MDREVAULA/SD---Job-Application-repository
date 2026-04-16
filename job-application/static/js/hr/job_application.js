// ================================
// HR Job Applications — JavaScript
// Filter · Search · Sort · Pagination · Upcoming interviews
// ================================

// ===== STATE =====
let currentFilter = 'all';
let currentSort   = 'date-desc';
let currentPage   = 1;
const CARDS_PER_PAGE = 8;
let allCards = [];

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    allCards = Array.from(document.querySelectorAll('.applicant-card'));
    applyFilters();
    filterUpcoming();   // init upcoming list too

    // Staggered entrance animation
    allCards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(16px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            card.style.opacity    = '1';
            card.style.transform  = 'translateY(0)';
        }, 60 + i * 40);
    });
});

// ===== FILTER + SEARCH =====
function applyFilters() {
    const term = (document.getElementById('applicantSearch')?.value || '').toLowerCase().trim();

    const filtered = allCards.filter(card => {
        const matchSearch = !term || card.dataset.name.includes(term);
        const matchStatus = currentFilter === 'all' || card.dataset.status === currentFilter;
        return matchSearch && matchStatus;
    });

    currentPage = 1;
    renderPage(filtered);
    renderPagination(filtered.length);
}

// ===== SORT =====
function applySort() {
    currentSort = document.getElementById('sortSelect')?.value || 'date-desc';

    allCards.sort((a, b) => {
        switch (currentSort) {
            case 'date-desc': return b.dataset.date.localeCompare(a.dataset.date);
            case 'date-asc':  return a.dataset.date.localeCompare(b.dataset.date);
            case 'name-asc':  return a.dataset.name.localeCompare(b.dataset.name);
            case 'name-desc': return b.dataset.name.localeCompare(a.dataset.name);
            default: return 0;
        }
    });

    // Re-attach sorted nodes
    const container = document.getElementById('applicantList');
    if (container) allCards.forEach(c => container.appendChild(c));

    applyFilters();
}

// ===== RENDER PAGE =====
function renderPage(filtered) {
    allCards.forEach(c => { c.style.display = 'none'; });

    const start = (currentPage - 1) * CARDS_PER_PAGE;
    const slice = filtered.slice(start, start + CARDS_PER_PAGE);

    slice.forEach(c => { c.style.display = 'block'; });

    if (slice.length > 0) {
        selectApplicant(slice[0]);
    }
}

// ===== PAGINATION UI =====
function renderPagination(total) {
    const totalPages = Math.max(1, Math.ceil(total / CARDS_PER_PAGE));
    const text   = document.getElementById('paginationText');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (text)    text.textContent = `Page ${currentPage} of ${totalPages}`;
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages;
}

function getFiltered() {
    const term = (document.getElementById('applicantSearch')?.value || '').toLowerCase().trim();
    return allCards.filter(c => {
        const matchSearch = !term || c.dataset.name.includes(term);
        const matchStatus = currentFilter === 'all' || c.dataset.status === currentFilter;
        return matchSearch && matchStatus;
    });
}

function nextPage() {
    const filtered    = getFiltered();
    const totalPages  = Math.ceil(filtered.length / CARDS_PER_PAGE);
    if (currentPage < totalPages) {
        currentPage++;
        renderPage(filtered);
        renderPagination(filtered.length);
        document.getElementById('applicantList')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        const filtered = getFiltered();
        renderPage(filtered);
        renderPagination(filtered.length);
        document.getElementById('applicantList')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ===== STATUS FILTER =====
function filterByStatus(btn, status) {
    document.querySelectorAll('.status-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = status;
    applyFilters();
}

// ===== SELECT APPLICANT =====
function selectApplicant(card) {
    document.querySelectorAll('.applicant-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');

    document.querySelectorAll('.applicant-detail-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById('detail-' + card.dataset.appId);
    if (panel) {
        panel.classList.add('active');
        if (window.innerWidth <= 1024) {
            panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

// ===== INTERVIEW FIELD TOGGLE =====
function toggleInterviewField(select, appId) {
    const field = document.getElementById('interview-field-' + appId);
    if (field) field.style.display = select.value === 'interview' ? 'block' : 'none';
}

// ===== ONLINE MEETING FIELDS TOGGLE =====
function toggleMeetingLink(select, appId) {
    const onlineFields = document.getElementById('online-fields-' + appId);
    if (onlineFields) onlineFields.style.display = select.value === 'online' ? 'block' : 'none';
}

// ===== UPCOMING INTERVIEWS: SEARCH + TIME FILTER =====
function filterUpcoming() {
    const term       = (document.getElementById('upcomingSearch')?.value || '').toLowerCase().trim();
    const timeFilter = document.getElementById('upcomingTimeFilter')?.value || 'all';

    const items = document.querySelectorAll('#upcomingList .upcoming-item');
    if (!items.length) return;

    const now   = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    // Week boundaries (Mon–Sun)
    const dayOfWeek   = today.getDay();
    const diffToMon   = (dayOfWeek === 0 ? -6 : 1 - dayOfWeek);
    const weekStart   = new Date(today); weekStart.setDate(today.getDate() + diffToMon);
    const weekEnd     = new Date(weekStart); weekEnd.setDate(weekStart.getDate() + 6);

    // Month boundaries
    const monthStart  = new Date(today.getFullYear(), today.getMonth(), 1);
    const monthEnd    = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    let visibleCount = 0;

    items.forEach(item => {
        const name     = item.dataset.upcomingName || '';
        const dateStr  = item.dataset.upcomingDate || '';   // YYYYMMDD

        const matchName = !term || name.includes(term);

        let matchTime = true;
        if (timeFilter !== 'all' && dateStr.length === 8) {
            const y = parseInt(dateStr.slice(0, 4), 10);
            const m = parseInt(dateStr.slice(4, 6), 10) - 1;
            const d = parseInt(dateStr.slice(6, 8), 10);
            const itemDate = new Date(y, m, d);

            if (timeFilter === 'week') {
                matchTime = itemDate >= weekStart && itemDate <= weekEnd;
            } else if (timeFilter === 'month') {
                matchTime = itemDate >= monthStart && itemDate <= monthEnd;
            }
        }

        const show = matchName && matchTime;
        item.style.display = show ? 'flex' : 'none';
        if (show) visibleCount++;
    });

    // Toggle no-results placeholder
    const noResults = document.getElementById('upcomingNoResults');
    const emptyBase = document.getElementById('upcomingEmpty');

    if (noResults) noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    if (emptyBase) emptyBase.style.display  = 'none';  // hidden once JS runs (real empty state is from Jinja)
}

// ===== KEYBOARD NAVIGATION =====
document.addEventListener('keydown', e => {
    const active  = document.querySelector('.applicant-card.active');
    if (!active) return;

    const visible = Array.from(document.querySelectorAll('.applicant-card'))
                         .filter(c => c.style.display !== 'none');
    const idx = visible.indexOf(active);
    let next = null;

    if ((e.key === 'ArrowDown' || e.key === 'ArrowRight') && idx < visible.length - 1) {
        e.preventDefault();
        next = visible[idx + 1];
    }
    if ((e.key === 'ArrowUp'   || e.key === 'ArrowLeft')  && idx > 0) {
        e.preventDefault();
        next = visible[idx - 1];
    }

    if (next) {
        selectApplicant(next);
        next.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});