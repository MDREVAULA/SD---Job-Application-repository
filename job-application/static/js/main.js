// Example JS: Search & Filter Jobs
document.addEventListener("DOMContentLoaded", function(){
    const searchInput = document.getElementById("jobSearchInput");
    if(searchInput){
        searchInput.addEventListener("input", function(){
            const query = searchInput.value.toLowerCase();
            const jobs = document.querySelectorAll(".job-card");
            jobs.forEach(job=>{
                const title = job.querySelector("h3,h4").innerText.toLowerCase();
                if(title.includes(query)){
                    job.style.display = "block";
                } else {
                    job.style.display = "none";
                }
            });
        });
    }
});