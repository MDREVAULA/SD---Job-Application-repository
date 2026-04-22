// ================================
// APPLICATION DETAIL - JavaScript
// Tab Switching with Smooth Transitions
// ================================

// ===== TAB SWITCHING =====
function switchTab(tabName, buttonElement) {
    // Hide all tab panels
    const allPanels = document.querySelectorAll('.tab-panel-new');
    allPanels.forEach(panel => {
        panel.classList.remove('active');
    });

    // Remove active state from all tabs
    const allTabs = document.querySelectorAll('.detail-tab-new');
    allTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab panel
    const selectedPanel = document.getElementById('tab-' + tabName);
    if (selectedPanel) {
        selectedPanel.classList.add('active');
    }

    // Add active state to clicked tab
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
}

// ===== ANIMATION ON LOAD =====
window.addEventListener('load', function() {
    // Fade in header card
    const headerCard = document.querySelector('.job-header-card-new');
    if (headerCard) {
        headerCard.style.opacity = '0';
        headerCard.style.transform = 'translateY(10px)';

        setTimeout(() => {
            headerCard.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            headerCard.style.opacity = '1';
            headerCard.style.transform = 'translateY(0)';
        }, 100);
    }

    // Fade in interview alert
    const interviewAlert = document.querySelector('.interview-alert-card');
    if (interviewAlert) {
        interviewAlert.style.opacity = '0';
        interviewAlert.style.transform = 'translateY(10px)';

        setTimeout(() => {
            interviewAlert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            interviewAlert.style.opacity = '1';
            interviewAlert.style.transform = 'translateY(0)';
        }, 200);
    }

    // Fade in tabs
    const tabs = document.querySelector('.detail-tabs-new');
    if (tabs) {
        tabs.style.opacity = '0';
        tabs.style.transform = 'translateY(10px)';

        setTimeout(() => {
            tabs.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            tabs.style.opacity = '1';
            tabs.style.transform = 'translateY(0)';
        }, 300);
    }

    // Fade in detail cards
    const detailCards = document.querySelectorAll('.detail-card-new');
    detailCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';

        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 400 + (index * 50));
    });
});

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // Switch to submission tab with '1' key
    if (e.key === '1' && !e.ctrlKey && !e.metaKey) {
        const submissionTab = document.querySelector('.detail-tab-new:first-child');
        if (submissionTab) {
            switchTab('application', submissionTab);
        }
    }

    // Switch to remarks tab with '2' key
    if (e.key === '2' && !e.ctrlKey && !e.metaKey) {
        const remarksTab = document.querySelector('.detail-tab-new:last-child');
        if (remarksTab) {
            switchTab('remarks', remarksTab);
        }
    }
});

// ===== SMOOTH SCROLL TO TOP ON TAB SWITCH =====
const tabButtons = document.querySelectorAll('.detail-tab-new');
tabButtons.forEach(button => {
    button.addEventListener('click', function() {
        // Smooth scroll to top of content area
        const wrapper = document.querySelector('.detail-page-wrapper');
        if (wrapper) {
            window.scrollTo({
                top: wrapper.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// ===== PRINT FUNCTIONALITY (Optional) =====
function printApplication() {
    window.print();
}

// Add print styles dynamically if needed
const printStyles = `
@media print {
    .job-view-nav,
    .detail-tabs-new,
    .back-link {
        display: none !important;
    }

    .tab-panel-new {
        display: block !important;
    }

    .detail-page-wrapper {
        padding: 0 !important;
    }
}
`;

function switchTab(tabName, btn) {
    document.querySelectorAll('.tab-panel-new').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.detail-tab-new').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tabName).classList.add('active');
    btn.classList.add('active');
}