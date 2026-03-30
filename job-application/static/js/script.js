document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("toggleBtn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    function openSidebar() {
        sidebar.classList.add("active");
        overlay.classList.add("active");
    }

    function closeSidebar() {
        sidebar.classList.remove("active");
        overlay.classList.remove("active");
    }

    toggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        if (sidebar.classList.contains("active")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    overlay.addEventListener("click", closeSidebar);
});

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleBtn');
    const closeBtn = document.getElementById('closeBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    // BUKAS: Gamit ang hamburger
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    });

    // SARA: Gamit ang X sa tabi ng Logo
    closeBtn.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });

    // SARA: Gamit ang overlay
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });
});


/* ============================= */
/* DROPDOWN MENU (RECRUITER) */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {

    const dropdownToggles = document.querySelectorAll(".dropdown-toggle");

    dropdownToggles.forEach(toggle => {

        toggle.addEventListener("click", function(e){

            e.preventDefault();

            const submenu = this.nextElementSibling;

            submenu.classList.toggle("open");

        });

    });

});

/* ============================= */
/*         FLASH MESSAGE         */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {

    const flashes = document.querySelectorAll(".flash");

    if (flashes.length > 0) {

        setTimeout(function () {

            flashes.forEach(function (flash) {

                flash.style.transition = "opacity 0.5s ease";
                flash.style.opacity = "0";

                setTimeout(function () {
                    flash.remove();
                }, 500);

            });

        }, 2000); // 4 seconds

    }

});

/* ============================= */
/*        THEME TOGGLE           */
/* ============================= */

(function () {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
})();

document.addEventListener('DOMContentLoaded', function () {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (theme === 'light') {
            themeIcon.className = 'fas fa-sun';
        } else {
            themeIcon.className = 'fas fa-moon';
        }
    }

    // Apply icon on load
    const currentTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(currentTheme);

    themeToggleBtn.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
});