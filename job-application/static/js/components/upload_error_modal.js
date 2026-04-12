/**
 * upload_error_modal.js
 * ---------------------
 * Shared utility for showing the upload error popup.
 * Used by profile_picture_modal.js and company_logo_modal.js.
 *
 * Place at: static/js/components/upload_error_modal.js
 * Load in: templates/layout.html  (before the two modal scripts)
 */

(function (global) {

    /**
     * showUploadError(options)
     *
     * options = {
     *   title      : string  — headline, e.g. "File Too Large"
     *   body       : string  — description sentence
     *   meta       : string  — small pill text, e.g. "Max size: 10MB · JPG, PNG"
     *   onRetry    : fn      — called when user clicks "Choose Another File"
     * }
     */
    function showUploadError(options) {
        const overlay   = document.getElementById('uploadErrorOverlay');
        const titleEl   = document.getElementById('uploadErrorTitle');
        const bodyEl    = document.getElementById('uploadErrorBody');
        const metaEl    = document.getElementById('uploadErrorMeta');
        const metaText  = document.getElementById('uploadErrorMetaText');
        const retryBtn  = document.getElementById('uploadErrorRetryBtn');

        if (!overlay) return; // guard: snippet not in page

        titleEl.textContent  = options.title  || 'Invalid File';
        bodyEl.textContent   = options.body   || 'This file cannot be uploaded.';
        metaText.textContent = options.meta   || '';

        // Show/hide meta pill
        metaEl.style.display = options.meta ? 'inline-flex' : 'none';

        // Wire retry button
        if (options.onRetry) {
            retryBtn.onclick = function () {
                closeUploadError();
                options.onRetry();
            };
        } else {
            retryBtn.onclick = closeUploadError;
        }

        overlay.classList.add('open');

        // Close on backdrop click
        overlay.onclick = function (e) {
            if (e.target === overlay) closeUploadError();
        };
    }

    function closeUploadError() {
        const overlay = document.getElementById('uploadErrorOverlay');
        if (overlay) overlay.classList.remove('open');
    }

    // Expose globally
    global.showUploadError  = showUploadError;
    global.closeUploadError = closeUploadError;

})(window);