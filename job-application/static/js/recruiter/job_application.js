/* ============================================================
   RECRUITER — Job Application List JS
   Features: collapsible cards, search by name, sort
   ============================================================ */

   let currentSort = 'date-desc';
   let currentStatus = 'all';
   
   // ── Card collapse / expand ──────────────────────────────────
   
   function toggleCard(headerEl) {
       const card = headerEl.closest('.app-card');
       const body = card.querySelector('.app-card-body');
       const icon = headerEl.querySelector('.card-toggle-icon i');
       const isOpen = card.classList.contains('card-open');
   
       if (isOpen) {
           // Collapse
           body.style.maxHeight = body.scrollHeight + 'px'; // pin before transition
           requestAnimationFrame(() => {
               body.style.maxHeight = '0';
               body.style.opacity  = '0';
           });
           card.classList.remove('card-open');
           icon.style.transform = 'rotate(0deg)';
       } else {
           // Expand
           body.style.maxHeight = body.scrollHeight + 'px';
           body.style.opacity   = '1';
           card.classList.add('card-open');
           icon.style.transform = 'rotate(180deg)';
   
           // After transition ends, remove fixed max-height so inner content
           // (e.g. textareas being resized) isn't clipped
           body.addEventListener('transitionend', function onEnd() {
               if (card.classList.contains('card-open')) {
                   body.style.maxHeight = 'none';
               }
               body.removeEventListener('transitionend', onEnd);
           });
       }
   }
   
   // ── Status filter tabs ──────────────────────────────────────
   
   function filterByStatus(status) {
       currentStatus = status;
       const tabs = document.querySelectorAll('.filter-tab');
       tabs.forEach(tab => {
           tab.classList.toggle('active', tab.getAttribute('data-status') === status);
       });
       applyFilters();
   }
   
   // ── Search ──────────────────────────────────────────────────
   
   function clearSearch() {
       const input = document.getElementById('applicantSearch');
       input.value = '';
       document.getElementById('searchClear').style.display = 'none';
       applyFilters();
   }
   
   // ── Sort ────────────────────────────────────────────────────
   
   function setSort(sortKey) {
       currentSort = sortKey;
       document.querySelectorAll('.sort-btn').forEach(btn => {
           btn.classList.toggle('active', btn.getAttribute('data-sort') === sortKey);
       });
       applyFilters();
   }
   
   // ── Core: filter + sort + render ───────────────────────────
   
   function applyFilters() {
       const searchVal = (document.getElementById('applicantSearch').value || '').toLowerCase().trim();
       const clearBtn  = document.getElementById('searchClear');
       if (clearBtn) clearBtn.style.display = searchVal ? 'flex' : 'none';
   
       const container = document.getElementById('applicationsContainer');
       if (!container) return;
   
       // Remove any existing no-results message
       const existing = container.querySelector('.no-results-state');
       if (existing) existing.remove();
   
       // Gather all cards
       const cards = Array.from(document.querySelectorAll('.app-card'));
   
       // 1. Determine visibility
       let visibleCards = [];
       cards.forEach(card => {
           const cardStatus = card.getAttribute('data-status');
           const cardName   = card.getAttribute('data-name') || '';
   
           const statusMatch = currentStatus === 'all' || cardStatus === currentStatus;
           const searchMatch = !searchVal || cardName.includes(searchVal);
   
           if (statusMatch && searchMatch) {
               card.style.display = '';
               visibleCards.push(card);
           } else {
               card.style.display = 'none';
           }
       });
   
       // 2. Sort visible cards
       visibleCards.sort((a, b) => {
           if (currentSort === 'date-desc') {
               return (b.getAttribute('data-date') || '0').localeCompare(a.getAttribute('data-date') || '0');
           } else if (currentSort === 'date-asc') {
               return (a.getAttribute('data-date') || '0').localeCompare(b.getAttribute('data-date') || '0');
           } else if (currentSort === 'name-asc') {
               return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
           } else if (currentSort === 'name-desc') {
               return (b.getAttribute('data-name') || '').localeCompare(a.getAttribute('data-name') || '');
           }
           return 0;
       });
   
       // 3. Re-insert in sorted order
       visibleCards.forEach(card => container.appendChild(card));
   
       // 4. Update results count
       const resultsEl = document.getElementById('resultsCount');
       if (resultsEl) {
           if (searchVal) {
               resultsEl.textContent = visibleCards.length === 0
                   ? 'No results'
                   : `${visibleCards.length} result${visibleCards.length !== 1 ? 's' : ''}`;
           } else {
               resultsEl.textContent = '';
           }
       }
   
       // 5. Show empty state if nothing visible
       if (visibleCards.length === 0) {
           const statusMessages = {
               all:       { icon: 'fa-search',        title: 'No Matching Applicants',  message: 'No applicants match your search.' },
               pending:   { icon: 'fa-clock',          title: 'No Pending Applicants',   message: 'There are no applications with pending status.' },
               interview: { icon: 'fa-calendar-check', title: 'No Interview Applicants', message: 'There are no applications scheduled for interview.' },
               accepted:  { icon: 'fa-check-circle',   title: 'No Accepted Applicants',  message: 'There are no accepted applications.' },
               rejected:  { icon: 'fa-times-circle',   title: 'No Rejected Applicants',  message: 'There are no rejected applications.' }
           };
           const m = statusMessages[currentStatus] || statusMessages.all;
           const emptyState = document.createElement('div');
           emptyState.className = 'no-results-state empty-state';
           emptyState.innerHTML = `<i class="fas ${m.icon}"></i><h3>${m.title}</h3><p>${m.message}</p>`;
           container.appendChild(emptyState);
       }
   }
   
   // ── Tab counts ──────────────────────────────────────────────
   
   function countApplications() {
       const cards = document.querySelectorAll('.app-card');
       const counts = { pending: 0, interview: 0, accepted: 0, rejected: 0 };
       cards.forEach(card => {
           const s = card.getAttribute('data-status');
           if (counts.hasOwnProperty(s)) counts[s]++;
       });
       document.getElementById('tabPendingCount').textContent   = counts.pending;
       document.getElementById('tabInterviewCount').textContent = counts.interview;
       document.getElementById('tabAcceptedCount').textContent  = counts.accepted;
       document.getElementById('tabRejectedCount').textContent  = counts.rejected;
   }
   
   // ── Description toggle ──────────────────────────────────────
   
   function toggleDescription() {
       const wrapper = document.getElementById('descriptionWrapper');
       const btn     = document.getElementById('toggleDescBtn');
       const text    = document.getElementById('toggleDescText');
       const isCollapsed = wrapper.classList.contains('collapsed');
       if (isCollapsed) {
           wrapper.classList.remove('collapsed');
           text.textContent = 'Show Less';
           btn.classList.add('expanded');
       } else {
           wrapper.classList.add('collapsed');
           text.textContent = 'Show More';
           btn.classList.remove('expanded');
           wrapper.closest('.job-description-full').scrollIntoView({ behavior: 'smooth', block: 'start' });
       }
   }
   
   // ── Status select (show/hide interview scheduler) ───────────
   
   function onStatusChange(selectEl) {
       const appId = selectEl.id.replace('status-', '');
       const scheduleInline = document.getElementById('scheduleInline-' + appId);
       if (scheduleInline) {
           scheduleInline.style.display = selectEl.value === 'interview' ? 'block' : 'none';
       }
   }
   
   // ── Init ────────────────────────────────────────────────────
   
   document.addEventListener('DOMContentLoaded', function () {
       countApplications();
   
       // Description toggle init
       const wrapper = document.getElementById('descriptionWrapper');
       const btn     = document.getElementById('toggleDescBtn');
       if (wrapper && btn) {
           if (wrapper.scrollHeight > 80) {
               wrapper.classList.add('collapsed');
               btn.style.display = 'flex';
           } else {
               btn.style.display = 'none';
               const fade = document.getElementById('descriptionFade');
               if (fade) fade.style.display = 'none';
           }
       }
   
       // Status select listeners
       document.querySelectorAll('.status-select').forEach(select => {
           select.addEventListener('change', function () { onStatusChange(this); });
       });
   
       // Init all cards: closed by default, set up body transition
       document.querySelectorAll('.app-card').forEach((card, index) => {
           const body = card.querySelector('.app-card-body');
           if (body) {
               body.style.maxHeight = '0';
               body.style.opacity   = '0';
               body.style.overflow  = 'hidden';
               body.style.transition = 'max-height 0.35s ease, opacity 0.25s ease';
           }
           // Subtle stagger fade-in for the card shells
           card.style.opacity   = '0';
           card.style.transform = 'translateY(16px)';
           setTimeout(() => {
               card.style.transition = 'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease';
               card.style.opacity    = '1';
               card.style.transform  = 'translateY(0)';
           }, 60 * index);
       });
   
       // Initial sort
       applyFilters();
   });