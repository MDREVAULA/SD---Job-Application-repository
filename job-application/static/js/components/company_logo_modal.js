/**
 * company_logo_modal.js
 * ---------------------
 * Free-crop modal for company logos (no fixed aspect ratio).
 * Requires: upload_error_modal.js loaded before this script.
 *
 * Size limit : 10 MB
 * Allowed    : any image/* (jpg, png, gif, webp …)
 * Output     : PNG if transparent, JPEG otherwise
 */

(function () {

    const MAX_MB    = 10;
    const MAX_BYTES = MAX_MB * 1024 * 1024;

    let logoCropper = null;

    const fileInput   = document.getElementById('logoFileInput');
    const backdrop    = document.getElementById('logoCropBackdrop');
    const cropImg     = document.getElementById('logoCropImage');
    const saveBtn     = document.getElementById('logoCropSaveBtn');
    const cancelBtn1  = document.getElementById('logoCancelBtn1');
    const cancelBtn2  = document.getElementById('logoCancelBtn2');
    const uploadForm  = document.getElementById('logoUploadForm');
    const hiddenInput = document.getElementById('logoCroppedData');

    // Hide on load (before CSS transition kicks in)
    if (backdrop) backdrop.style.display = 'none';

    /* ── open modal ── */
    function openModal(src) {
        cropImg.src = src;
        backdrop.style.display = 'flex';

        // Two rAF ticks so display:flex is painted before opacity transitions
        requestAnimationFrame(() => requestAnimationFrame(() => {
            backdrop.classList.add('active');
        }));

        cropImg.onload = function () {
            if (logoCropper) logoCropper.destroy();
            logoCropper = new Cropper(cropImg, {
                aspectRatio          : NaN,   // free ratio
                viewMode             : 1,
                dragMode             : 'move',
                autoCropArea         : 0.9,
                cropBoxMovable       : true,
                cropBoxResizable     : true,
                toggleDragModeOnDblclick: false,
            });
        };
    }

    /* ── close modal ── */
    function closeModal() {
        backdrop.classList.remove('active');
        setTimeout(() => { backdrop.style.display = 'none'; }, 250);
        if (logoCropper) { logoCropper.destroy(); logoCropper = null; }
        fileInput.value = '';
        cropImg.src = '';
    }

    /* ── file selected ── */
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            // Type check
            if (!file.type.startsWith('image/')) {
                showUploadError({
                    title   : 'Invalid File Type',
                    body    : 'Your company logo must be an image file (JPG, PNG, WEBP, etc.).',
                    meta    : 'Accepted formats: JPG · PNG · WEBP · GIF',
                    onRetry : () => fileInput.click(),
                });
                fileInput.value = '';
                return;
            }

            // Size check
            if (file.size > MAX_BYTES) {
                const sizeMB = (file.size / 1024 / 1024).toFixed(1);
                showUploadError({
                    title   : 'File Too Large',
                    body    : `Your logo is ${sizeMB} MB, which exceeds the ${MAX_MB} MB limit. Please choose a smaller image.`,
                    meta    : `Max size: ${MAX_MB} MB`,
                    onRetry : () => fileInput.click(),
                });
                fileInput.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = e => openModal(e.target.result);
            reader.readAsDataURL(file);
        });
    }

    /* ── save cropped logo ── */
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            if (!logoCropper) return;

            const canvas = logoCropper.getCroppedCanvas({
                maxWidth              : 800,
                maxHeight             : 800,
                imageSmoothingEnabled : true,
                imageSmoothingQuality : 'high',
            });

            // Preserve transparency for PNG logos
            const ctx       = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const hasAlpha  = Array.from(imageData.data)
                .some((val, idx) => idx % 4 === 3 && val < 255);

            hiddenInput.value = hasAlpha
                ? canvas.toDataURL('image/png')
                : canvas.toDataURL('image/jpeg', 0.85);

            uploadForm.submit();
        });
    }

    /* ── cancel ── */
    if (cancelBtn1) cancelBtn1.addEventListener('click', closeModal);
    if (cancelBtn2) cancelBtn2.addEventListener('click', closeModal);
    if (backdrop)   backdrop.addEventListener('click', e => {
        if (e.target === backdrop) closeModal();
    });

})();