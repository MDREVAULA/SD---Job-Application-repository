// Add admin-page class to main-content to scope CSS
document.addEventListener("DOMContentLoaded", function () {
    const main = document.querySelector(".main-content");
    if (main) main.classList.add("admin-page");
});