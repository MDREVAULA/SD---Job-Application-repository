document.addEventListener("DOMContentLoaded", function () {

    const steps = document.querySelectorAll(".form-step");
    const nextBtns = document.querySelectorAll(".next-btn");
    const backBtns = document.querySelectorAll(".back-btn");
    
    const roleSelect = document.getElementById("role");
    const step3Btn = document.getElementById("step3-btn");
    
    const form = document.querySelector("form");
    
    let currentStep = 0;
    
    
    /* SHOW STEP */
    
    function showStep(step){
    
        steps.forEach((s,i)=>{
            s.classList.remove("active");
    
            if(i === step){
                s.classList.add("active");
            }
    
        });
    
    }
    
    
    /* UPDATE STEP 3 BUTTON */
    
    function updateStep3Button(){

        if(roleSelect.value === "applicant"){
    
            step3Btn.textContent = "Register";
    
            step3Btn.classList.remove("next-btn");
            step3Btn.classList.add("register-button");
    
        }else{
    
            step3Btn.textContent = "Continue";
    
            step3Btn.classList.remove("register-button");
            step3Btn.classList.add("next-btn");
    
        }
    
    }
    
    
    /* NEXT BUTTON */
    
    nextBtns.forEach(btn=>{
        btn.addEventListener("click",()=>{
    
            const role = roleSelect.value;
    
            // Applicant registers after Address step
            if(role === "applicant" && currentStep === 2){
                form.submit();
                return;
            }
    
            currentStep++;
    
            if(currentStep >= steps.length){
                currentStep = steps.length - 1;
            }
    
            showStep(currentStep);
    
        });
    });
    
    
    /* BACK BUTTON */
    
    backBtns.forEach(btn=>{
        btn.addEventListener("click",()=>{
    
            currentStep--;
    
            if(currentStep < 0){
                currentStep = 0;
            }
    
            showStep(currentStep);
    
        });
    });
    
    
    /* ROLE CHANGE */
    
    roleSelect.addEventListener("change",()=>{
    
        currentStep = 0;
        showStep(currentStep);
        updateStep3Button();
    
    });
    
    
    /* INITIAL LOAD */
    
    showStep(currentStep);
    updateStep3Button();
    
    
    /* COUNTRY SELECT SEARCH */
    
    $('.country-select').select2({
        placeholder: "Search or select a country",
        allowClear: true
    });
    
    });