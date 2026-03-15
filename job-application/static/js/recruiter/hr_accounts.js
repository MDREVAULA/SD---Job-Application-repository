// ================================
//  HR ACCOUNTS PAGE SCRIPTS
// ================================

// Copy password to clipboard
function copyPassword() {
    const passwordInput = document.getElementById('tempPassword');
    passwordInput.select();
    passwordInput.setSelectionRange(0, 99999); // For mobile devices
    
    // Modern clipboard API
    navigator.clipboard.writeText(passwordInput.value).then(() => {
        const btn = event.target.closest('button');
        const originalHTML = btn.innerHTML;
        
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('copied');
        
        // Keep the "Copied" message for 2 seconds, but DON'T hide the password box
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('copied');
        }, 2000);
    }).catch(() => {
        // Fallback for older browsers
        document.execCommand('copy');
        const btn = event.target.closest('button');
        const originalHTML = btn.innerHTML;
        
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('copied');
        }, 2000);
    });
}

// Close password box manually (optional)
function closePasswordBox() {
    const passwordBox = document.getElementById('tempPasswordBox');
    if (confirm('Are you sure you want to dismiss this? The password won\'t be shown again!')) {
        passwordBox.style.display = 'none';
    }
}

// Auto-scroll to password box when it appears
window.addEventListener('DOMContentLoaded', function() {
    const passwordBox = document.getElementById('tempPasswordBox');
    if (passwordBox) {
        // Scroll to password box smoothly
        passwordBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Stop the pulse animation after 6 seconds
        setTimeout(() => {
            passwordBox.style.animation = 'none';
        }, 6000);
    }
});