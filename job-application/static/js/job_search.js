// ===============================
// JOB SEARCH + FIELD FILTER
// ===============================

document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("jobSearchInput");
    const fieldFilter = document.getElementById("fieldFilter");
    const jobs = document.querySelectorAll(".job-card");

    function filterJobs() {

        const searchQuery = searchInput ? searchInput.value.toLowerCase() : "";
        const fieldValue = fieldFilter ? fieldFilter.value.toLowerCase() : "";

        jobs.forEach(job => {

            const titleElement = job.querySelector("h3, h4");
            const title = titleElement ? titleElement.innerText.toLowerCase() : "";

            const field = job.dataset.field ? job.dataset.field.toLowerCase() : "";

            const matchesSearch = title.includes(searchQuery);
            const matchesField = fieldValue === "" || field.includes(fieldValue);

            if (matchesSearch && matchesField) {
                job.style.display = "block";
            } else {
                job.style.display = "none";
            }

        });

    }

    // SEARCH EVENT
    if (searchInput) {
        searchInput.addEventListener("input", filterJobs);
    }

    // FIELD FILTER EVENT
    if (fieldFilter) {
        fieldFilter.addEventListener("change", filterJobs);
    }

});