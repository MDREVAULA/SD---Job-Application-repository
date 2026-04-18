// ============================================
// About Us Page - Sticky Navigation
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');

    // Smooth scroll to sections
    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 90; 
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Throttle scroll event for performance
    let isScrolling = false;
    window.addEventListener('scroll', function () {
        if (!isScrolling) {
            window.requestAnimationFrame(function () {
                updateActiveNav();
                isScrolling = false;
            });
            isScrolling = true;
        }
    });

    // Initial check
    updateActiveNav();
});