document.addEventListener("DOMContentLoaded", function () {

    const steps = document.querySelectorAll(".form-step");
    const nextBtns = document.querySelectorAll(".next-btn");
    const backBtns = document.querySelectorAll(".back-btn");

    const roleSelect = document.getElementById("role");
    const step3Btn = document.getElementById("step3-btn");

    const form = document.querySelector("form");

    let currentStep = 0;

    // =========================
    // REGISTER FORM ONLY
    // =========================
    const isRegisterPage = roleSelect && step3Btn && steps.length > 0;

    if (isRegisterPage) {

        // =========================
        // SHOW STEP
        // =========================
        function showStep(step) {
            steps.forEach((s, i) => {
                s.classList.remove("active");
                if (i === step) s.classList.add("active");
            });
            updateProgressIndicator();
        }

        // =========================
        // UPDATE PROGRESS INDICATOR
        // =========================
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

                if (role === "applicant" && i === 3) {
                    step.style.display = "none";
                } else {
                    step.style.display = "flex";
                }
            });

            if (progressLine) {
                const percentage = (currentStep / (totalSteps - 1)) * 100;
                progressLine.style.width = percentage + "%";
            }
        }

        // =========================
        // UPDATE STEP 3 BUTTON
        // =========================
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

        // =========================
        // SHOW FIELD ERROR
        // =========================
        function showFieldError(input, message) {
            clearFieldError(input);
            input.style.borderColor = "#ff4d4d";
            const error = document.createElement("div");
            error.className = "field-error";
            error.textContent = message;
            input.parentNode.appendChild(error);
        }

        function clearFieldError(input) {
            input.style.borderColor = "";
            const existing = input.parentNode.querySelector(".field-error");
            if (existing) existing.remove();
        }

        // =========================
        // VALIDATE STEP
        // =========================
        function validateStep(stepIndex) {
            const step = steps[stepIndex];
            let valid = true;

            step.querySelectorAll(".field-error").forEach(e => e.remove());
            step.querySelectorAll(".form-input").forEach(i => i.style.borderColor = "");

            const requiredFields = step.querySelectorAll("[required]");
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    showFieldError(field, "This field is required.");
                    valid = false;
                }
            });

            if (stepIndex === 0) {
                const password = step.querySelector("[name='password']");
                if (password && password.value.length > 0 && password.value.length < 8) {
                    showFieldError(password, "Password must be at least 8 characters.");
                    valid = false;
                }
            }

            return valid;
        }

        // =========================
        // CHECK EMAIL/USERNAME (AJAX)
        // =========================
        async function checkEmailAndUsername() {
            const email = document.querySelector("[name='email']").value.trim();
            const username = document.querySelector("[name='username']").value.trim();

            try {
                const response = await fetch("/check-availability", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, username })
                });

                const data = await response.json();
                let valid = true;

                if (data.email_taken) {
                    showFieldError(document.querySelector("[name='email']"), "This email is already registered.");
                    valid = false;
                }

                if (data.username_taken) {
                    showFieldError(document.querySelector("[name='username']"), "This username is already taken.");
                    valid = false;
                }

                return valid;

            } catch (err) {
                return true;
            }
        }

        // =========================
        // NEXT BUTTON
        // =========================
        nextBtns.forEach(btn => {
            btn.addEventListener("click", async () => {
                const role = roleSelect.value;

                if (!validateStep(currentStep)) return;

                if (currentStep === 0) {
                    btn.textContent = "Checking...";
                    btn.disabled = true;

                    const available = await checkEmailAndUsername();

                    btn.textContent = "Continue";
                    btn.disabled = false;

                    if (!available) return;
                }

                if (role === "applicant" && currentStep === 2) return;

                currentStep++;
                if (currentStep >= steps.length) currentStep = steps.length - 1;
                showStep(currentStep);
            });
        });

        // =========================
        // BACK BUTTON
        // =========================
        backBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                currentStep--;
                if (currentStep < 0) currentStep = 0;
                showStep(currentStep);
            });
        });

        // =========================
        // ROLE CHANGE
        // =========================
        roleSelect.addEventListener("change", () => {
            updateStep3Button();
            updateProgressIndicator();
        });

        // =========================
        // PREVENT ENTER KEY SUBMITTING EARLY
        // =========================
        if (form) {
            form.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    const role = roleSelect.value;
                    const finalStep = role === "applicant" ? 2 : 3;

                    if (currentStep === finalStep) {
                        const activeElement = document.activeElement;
                        if (activeElement.type === "submit" || activeElement.classList.contains("register-button")) {
                            return;
                        }
                        form.submit();
                    } else {
                        e.preventDefault();
                        const currentStepElement = steps[currentStep];
                        const nextBtn = currentStepElement.querySelector(".next-btn");
                        if (nextBtn) nextBtn.click();
                    }
                }
            });
        }

        // =========================
        // CLEAR ERROR ON INPUT
        // =========================
        document.querySelectorAll(".form-input").forEach(input => {
            input.addEventListener("input", () => clearFieldError(input));
            input.addEventListener("change", () => clearFieldError(input));
        });

        // =========================
        // INITIAL LOAD
        // =========================
        showStep(currentStep);
        updateStep3Button();

        // =========================
        // COUNTRY SELECT SEARCH
        // =========================
        if (typeof $.fn.select2 !== "undefined") {
            $(".country-select").select2({
                placeholder: "Search or select a country",
                allowClear: true
            });
        }

    }
    // =========================
    // END REGISTER FORM ONLY
    // =========================


    // =========================
    // COMPANY LOGO PREVIEW
    // Runs on register AND google recruiter profile pages
    // =========================
    const logoInput = document.getElementById("company_logo");
    if (logoInput) {
        logoInput.addEventListener("change", function () {
            const file = this.files[0];
            const container = document.getElementById("logo-preview-container");
            const preview = document.getElementById("logo-preview");

            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    container.style.display = "block";
                };
                reader.readAsDataURL(file);
            } else {
                container.style.display = "none";
                preview.src = "";
            }
        });
    }


    // =========================
    // COMPANY PROOF PREVIEW
    // Runs on register AND google recruiter profile pages
    // =========================
    const proofInput = document.getElementById("company_proof");
    if (proofInput) {
        proofInput.addEventListener("change", function () {
            const file = this.files[0];
            const container = document.getElementById("proof-preview-container");
            const previewImg = document.getElementById("proof-preview-img");
            const previewFile = document.getElementById("proof-preview-file");
            const fileName = document.getElementById("proof-file-name");
            const fileSize = document.getElementById("proof-file-size");
            const fileIcon = document.getElementById("proof-file-icon");
            const fileLink = document.getElementById("proof-file-link");

            if (fileLink.href && fileLink.href.startsWith("blob:")) {
                URL.revokeObjectURL(fileLink.href);
            }

            if (file) {
                container.style.display = "block";
                const isImage = file.type.startsWith("image/");

                if (isImage) {
                    previewFile.style.display = "none";
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        previewImg.src = e.target.result;
                        previewImg.style.display = "block";
                    };
                    reader.readAsDataURL(file);
                } else {
                    previewImg.style.display = "none";
                    previewImg.src = "";

                    if (file.type === "application/pdf") {
                        fileIcon.textContent = "📕";
                    } else if (file.name.endsWith(".doc") || file.name.endsWith(".docx")) {
                        fileIcon.textContent = "📘";
                    } else {
                        fileIcon.textContent = "📄";
                    }

                    const sizeInKB = (file.size / 1024).toFixed(1);
                    const sizeDisplay = sizeInKB > 1024
                        ? (sizeInKB / 1024).toFixed(2) + " MB"
                        : sizeInKB + " KB";

                    fileName.textContent = file.name;
                    fileSize.textContent = sizeDisplay;

                    const objectURL = URL.createObjectURL(file);
                    fileLink.href = objectURL;

                    previewFile.style.display = "flex";
                }
            } else {
                container.style.display = "none";
                previewImg.style.display = "none";
                previewImg.src = "";
                previewFile.style.display = "none";
            }
        });
    }

});