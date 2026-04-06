/* ============================= */
/*     REGISTER PAGE SCRIPT      */
/* Step 1 only — quick sign-up   */
/* ============================= */

document.addEventListener('DOMContentLoaded', function () {

    const form        = document.querySelector('.register-form');
    const emailInput  = document.querySelector('[name="email"]');
    const userInput   = document.querySelector('[name="username"]');
    const passInput   = document.getElementById('reg-password');
    const toggleBtn   = document.getElementById('togglePassword');
    const eyeIcon     = document.getElementById('eyeIcon');
    const strengthFill = document.getElementById('strengthFill');
    const submitBtn   = document.getElementById('registerBtn');

    if (!form) return;

    /* ─── Password visibility toggle ─── */
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            const isText = passInput.type === 'text';
            passInput.type = isText ? 'password' : 'text';
            eyeIcon.className = isText ? 'fas fa-eye' : 'fas fa-eye-slash';
        });
    }

    /* ─── Password strength bar ─── */
    if (passInput && strengthFill) {
        passInput.addEventListener('input', function () {
            const val = passInput.value;
            let strength = 0;

            if (val.length >= 8)               strength++;
            if (/[A-Z]/.test(val))             strength++;
            if (/[0-9]/.test(val))             strength++;
            if (/[^A-Za-z0-9]/.test(val))      strength++;

            const pct   = (strength / 4) * 100;
            const color = strength <= 1 ? '#f87171'
                        : strength === 2 ? '#F1B24A'
                        : strength === 3 ? '#9DC88D'
                        :                  '#4D774E';

            strengthFill.style.width           = pct + '%';
            strengthFill.style.backgroundColor = color;
        });
    }

    /* ─── Show / clear field error ─── */
    function showError(id, msg) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = msg;
        el.classList.add('visible');
        const input = el.closest('.register-field')?.querySelector('.register-input');
        if (input) input.classList.add('is-error');
    }

    function clearError(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = '';
        el.classList.remove('visible');
        const input = el.closest('.register-field')?.querySelector('.register-input');
        if (input) input.classList.remove('is-error');
    }

    /* Clear on type */
    if (userInput)  userInput.addEventListener('input',  () => clearError('err-username'));
    if (emailInput) emailInput.addEventListener('input',  () => clearError('err-email'));
    if (passInput)  passInput.addEventListener('input',  () => clearError('err-password'));

    /* ─── Availability check (debounced) ─── */
    let checkTimer = null;

    function scheduleCheck() {
        clearTimeout(checkTimer);
        checkTimer = setTimeout(checkAvailability, 600);
    }

    async function checkAvailability() {
        const email    = emailInput  ? emailInput.value.trim()  : '';
        const username = userInput   ? userInput.value.trim()   : '';

        if (!email && !username) return;

        try {
            const res  = await fetch('/check-availability', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email, username })
            });
            const data = await res.json();

            if (data.email_taken)    showError('err-email',    'This email is already registered.');
            else                     clearError('err-email');

            if (data.username_taken) showError('err-username', 'This username is already taken.');
            else                     clearError('err-username');

        } catch (_) { /* silent fail */ }
    }

    if (emailInput)  emailInput.addEventListener('blur',  scheduleCheck);
    if (userInput)   userInput.addEventListener('blur',   scheduleCheck);

    /* ─── Client-side validation before submit ─── */
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        let valid = true;

        const username = userInput  ? userInput.value.trim()  : '';
        const email    = emailInput ? emailInput.value.trim() : '';
        const password = passInput  ? passInput.value          : '';

        if (!username) {
            showError('err-username', 'Username is required.');
            valid = false;
        }

        if (!email) {
            showError('err-email', 'Email is required.');
            valid = false;
        }

        if (!password || password.length < 8) {
            showError('err-password', 'Password must be at least 8 characters.');
            valid = false;
        }

        if (!valid) return;

        /* Live availability check on submit */
        submitBtn.disabled   = true;
        submitBtn.innerHTML  = '<i class="fas fa-spinner fa-spin"></i> Checking...';

        try {
            const res  = await fetch('/check-availability', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email, username })
            });
            const data = await res.json();

            if (data.email_taken) {
                showError('err-email', 'This email is already registered.');
                valid = false;
            }
            if (data.username_taken) {
                showError('err-username', 'This username is already taken.');
                valid = false;
            }
        } catch (_) { /* silent fail */ }

        if (!valid) {
            submitBtn.disabled  = false;
            submitBtn.innerHTML = '<i class="fas fa-arrow-right"></i> Create Account';
            return;
        }

        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
        form.submit();
    });

});