document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const questionsList = document.getElementById("questionsList");

    const qaData = [
        {
            question: "How to login?",
            answer: "Click the login button, and then fill in the required information.",
            photo: "#"  /* optional ang pag-i-include ng photo */
        },
        {
            question: "How to create my account/signup",
            answer: "Click the signup button, and then fill in the required information.",    
        },
    ];

    function renderQuestions(filterText = "") {
        questionsList.innerHTML = "";

        const filtered = qaData.filter(item =>
            item.question.toLowerCase().includes(filterText.toLowerCase())
        );

        filtered.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item.question;

            const answerDiv = document.createElement("div");
            answerDiv.className = "answer";

            // Add answer text
            const p = document.createElement("p");
            p.textContent = item.answer;
            answerDiv.appendChild(p);

            // Add image if exists
            if (item.photo) {
                const img = document.createElement("img");
                img.src = item.photo;
                img.alt = "Visual guide";
                img.style.maxWidth = "100%";
                img.style.marginTop = "10px";
                img.style.borderRadius = "8px";
                answerDiv.appendChild(img);
            }

            li.appendChild(answerDiv);

            li.addEventListener("click", () => {
                answerDiv.style.display = answerDiv.style.display === "none" ? "block" : "none";
            });

            questionsList.appendChild(li);
        });
    }

    renderQuestions();

    searchInput.addEventListener("input", (e) => {
        renderQuestions(e.target.value);
    });
});