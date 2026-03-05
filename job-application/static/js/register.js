function toggleFields() {
    const role = document.getElementById('role').value;

    const recruiterFields = document.getElementById('recruiter-fields');
    const applicantFields = document.getElementById('applicant-fields');

    if (role === "recruiter") {
        recruiterFields.style.display = "block";
        applicantFields.style.display = "none";
    } else {
        recruiterFields.style.display = "none";
        applicantFields.style.display = "block";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    toggleFields();
});

$(document).ready(function () {
    $('.country-select').select2({
        placeholder: "Search or select a country",
        allowClear: true
    });
});