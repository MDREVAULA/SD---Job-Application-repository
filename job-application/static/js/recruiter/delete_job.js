// ===================================
// DELETE JOB MODAL FUNCTIONALITY
// ===================================

let deleteFormToSubmit = null;

function openDeleteModal(button) {
    const modal = document.getElementById('deleteModal');
    const form = button.closest('form');
    
    deleteFormToSubmit = form;
    
    if (modal) {
        modal.style.display = 'flex';
        
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    
    deleteFormToSubmit = null;
    
    if (modal) {
        modal.style.display = 'none';
        
        // Re-enable body scroll
        document.body.style.overflow = '';
    }
}

// Confirm delete button
document.addEventListener('DOMContentLoaded', function() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const modal = document.getElementById('deleteModal');
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (deleteFormToSubmit) {
                deleteFormToSubmit.submit();
            }
        });
    }
    
    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeDeleteModal();
            }
        });
    }
    
    // Close modal with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDeleteModal();
        }
    });
});