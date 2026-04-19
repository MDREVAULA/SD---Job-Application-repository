/**
 * Submit Documents Page JavaScript
 * Handles file preview and form submission
 */

(function() {
    'use strict';

    function previewFile(input, reqId) {
        const preview = document.getElementById('preview-' + reqId);
        if (!preview) return;

        if (input.files && input.files[0]) {
            const f = input.files[0];
            const sizeStr = f.size > 1048576
                ? (f.size / 1048576).toFixed(1) + ' MB'
                : Math.round(f.size / 1024) + ' KB';

            preview.innerHTML = `
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4D774E" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <p style="color:var(--text-primary);font-weight:600;margin:6px 0 2px;">${f.name}</p>
                <span>${sizeStr} — ready to upload</span>
            `;

            const zone = document.getElementById('zone-' + reqId);
            if (zone) {
                zone.style.borderColor = '#4D774E';
            }
        }
    }

    function initFileInputs() {
        const fileInputs = document.querySelectorAll('.emp-file-input');
        fileInputs.forEach(input => {
            const reqId = input.getAttribute('data-req-id');
            if (reqId) {
                input.addEventListener('change', function() {
                    previewFile(this, reqId);
                });
            }
        });
    }

    function initFormSubmit() {
        const form = document.getElementById('empSubmitForm');
        const btn = document.getElementById('empSubmitBtn');

        if (form && btn) {
            form.addEventListener('submit', function() {
                btn.disabled = true;
                btn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                        <line x1="12" y1="2" x2="12" y2="6"/>
                        <line x1="12" y1="18" x2="12" y2="22"/>
                        <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                        <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                        <line x1="2" y1="12" x2="6" y2="12"/>
                        <line x1="18" y1="12" x2="22" y2="12"/>
                        <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
                        <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
                    </svg>
                    Uploading...
                `;
            });
        }
    }

    function addSpinnerAnimation() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    function init() {
        initFileInputs();
        initFormSubmit();
        addSpinnerAnimation();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();