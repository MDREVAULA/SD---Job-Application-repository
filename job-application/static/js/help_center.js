document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    const searchInput = document.getElementById("searchInput");
    const questionsList = document.getElementById("questionsList");
    const questions = document.querySelectorAll("#questionsList li");
    const categoryBtns = document.querySelectorAll(".category-btn");
    const noResults = document.getElementById("noResults");
    
    let activeCategory = "all";

    // Toggle answer when clicking a question
    questions.forEach(li => {
        const questionHeader = li.querySelector(".question-header");
        
        questionHeader.addEventListener("click", () => {
            // Close other open questions (optional - remove if you want multiple open)
            questions.forEach(otherLi => {
                if (otherLi !== li && otherLi.classList.contains("active")) {
                    otherLi.classList.remove("active");
                }
            });
            
            // Toggle current question
            li.classList.toggle("active");
        });
    });

    // Category filter functionality
    categoryBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            // Update active button
            categoryBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Get selected category
            activeCategory = btn.getAttribute("data-category");
            
            // Filter questions
            filterQuestions();
        });
    });

    // Search functionality with highlighting
    searchInput.addEventListener("input", function() {
        filterQuestions();
    });

    function filterQuestions() {
        const filter = searchInput.value.toLowerCase();
        let visibleCount = 0;

        questions.forEach(li => {
            const questionText = li.querySelector(".question").textContent;
            const answerText = li.querySelector(".answer p").textContent;
            const category = li.getAttribute("data-category");
            
            const matchesSearch = questionText.toLowerCase().includes(filter) || 
                                 answerText.toLowerCase().includes(filter);
            const matchesCategory = activeCategory === "all" || category === activeCategory;

            if (matchesSearch && matchesCategory) {
                li.style.display = "block";
                visibleCount++;
                
                // Highlight matching text
                highlightText(li.querySelector(".question"), questionText, filter);
                highlightText(li.querySelector(".answer p"), answerText, filter);
            } else {
                li.style.display = "none";
                li.classList.remove("active");
            }
        });

        // Show/hide no results message
        if (visibleCount === 0) {
            noResults.style.display = "block";
            questionsList.style.display = "none";
            // Re-initialize icons for no results
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        } else {
            noResults.style.display = "none";
            questionsList.style.display = "block";
        }
    }

    function highlightText(element, originalText, searchTerm) {
        if (!searchTerm.trim()) {
            element.textContent = originalText;
            return;
        }

        const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi');
        const highlighted = originalText.replace(regex, '<mark>$1</mark>');
        element.innerHTML = highlighted;
    }

    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Contact support button (customize this to your needs)
    const supportBtn = document.querySelector(".support-btn");
    if (supportBtn) {
        supportBtn.addEventListener("click", () => {
            // Add your contact support logic here
            // For example: window.location.href = '/contact';
            alert("Contact support functionality - customize this to your needs!");
        });
    }

    // Auto-expand first question on load (optional)
    // if (questions.length > 0) {
    //     questions[0].classList.add("active");
    // }
});