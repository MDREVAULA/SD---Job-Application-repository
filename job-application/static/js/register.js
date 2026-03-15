document.addEventListener("DOMContentLoaded", function () {

    const steps = document.querySelectorAll(".form-step");
    const nextBtns = document.querySelectorAll(".next-btn");
    const backBtns = document.querySelectorAll(".back-btn");
    
    const roleSelect = document.getElementById("role");
    const step3Btn = document.getElementById("step3-btn");
    
    const form = document.querySelector("form");
    
    let currentStep = 0;
    
    /* SHOW STEP */
    
    function showStep(step) {
        steps.forEach((s, i) => {
            s.classList.remove("active");
            
            if (i === step) {
                s.classList.add("active");
            }
        });
        
        updateProgressIndicator();
    }
    
    /* UPDATE PROGRESS INDICATOR */
    
    function updateProgressIndicator() {
        const progressSteps = document.querySelectorAll(".progress-step");
        const progressLine = document.querySelector(".progress-line");
        
        const role = roleSelect.value;
        const totalSteps = role === "applicant" ? 3 : 4;
        
        progressSteps.forEach((step, i) => {
            step.classList.remove("active", "completed");
            
            if (i < currentStep) {
                step.classList.add("completed");
            } else if (i === currentStep) {
                step.classList.add("active");
            }
            
            // Hide step 4 for applicants
            if (role === "applicant" && i === 3) {
                step.style.display = "none";
            } else {
                step.style.display = "flex";
            }
        });
        
        // Update progress line width
        if (progressLine) {
            const percentage = (currentStep / (totalSteps - 1)) * 100;
            progressLine.style.width = percentage + "%";
        }
    }
    
    /* UPDATE STEP 3 BUTTON */
    
    function updateStep3Button() {
        if (roleSelect.value === "applicant") {
            step3Btn.textContent = "Register";
            step3Btn.classList.remove("next-btn");
            step3Btn.classList.add("register-button");
            step3Btn.type = "submit";
        } else {
            step3Btn.textContent = "Continue";
            step3Btn.classList.remove("register-button");
            step3Btn.classList.add("next-btn");
            step3Btn.type = "button";
        }
    }
    
    /* NEXT BUTTON */
    
    nextBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const role = roleSelect.value;
            
            // Applicant registers after Address step (handled by button type="submit")
            if (role === "applicant" && currentStep === 2) {
                return; // Form will submit naturally
            }
            
            currentStep++;
            
            if (currentStep >= steps.length) {
                currentStep = steps.length - 1;
            }
            
            showStep(currentStep);
        });
    });
    
    /* BACK BUTTON */
    
    backBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            currentStep--;
            
            if (currentStep < 0) {
                currentStep = 0;
            }
            
            showStep(currentStep);
        });
    });
    
    /* ROLE CHANGE */
    
    roleSelect.addEventListener("change", () => {
        currentStep = 0;
        showStep(currentStep);
        updateStep3Button();
    });
    
    /* PREVENT ENTER KEY FROM SUBMITTING FORM (except on final step) */
    
    form.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            const role = roleSelect.value;
            const finalStep = role === "applicant" ? 2 : 3;
            
            // Allow submit only on final step
            if (currentStep === finalStep) {
                // Check if the active element is the submit button
                const activeElement = document.activeElement;
                if (activeElement.type === "submit" || activeElement.classList.contains("register-button")) {
                    return; // Allow form submission
                }
                // Trigger form submission if on final step
                form.submit();
            } else {
                // Prevent default and move to next step
                e.preventDefault();
                
                // Find the next button in the current step and click it
                const currentStepElement = steps[currentStep];
                const nextBtn = currentStepElement.querySelector(".next-btn");
                
                if (nextBtn) {
                    nextBtn.click();
                }
            }
        }
    });
    
    /* INITIAL LOAD */
    
    showStep(currentStep);
    updateStep3Button();
    
    /* COUNTRY SELECT SEARCH */
    
    if (typeof $.fn.select2 !== 'undefined') {
        $('.country-select').select2({
            placeholder: "Search or select a country",
            allowClear: true
        });
    }

});