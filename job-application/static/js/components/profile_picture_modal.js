/**
 * profile_picture_modal.js
 * ------------------------
 * 1×1 crop modal for profile pictures.
 * Requires: upload_error_modal.js loaded before this script.
 *
 * Size limit : 10 MB  (matches server-side crop — no hard server check,
 *              but base64 payload would be enormous above this)
 * Allowed    : any image/* (jpg, png, gif, webp …)
 */

(function () {

    const MAX_MB       = 10;
    const MAX_BYTES    = MAX_MB * 1024 * 1024;

    let cropper = null;

    const fileInput   = document.getElementById('pfpFileInput');
    const backdrop    = document.getElementById('cropModalBackdrop');
    const cropImg     = document.getElementById('cropImage');
    const saveBtn     = document.getElementById('cropSaveBtn');
    const cancelBtn1  = document.getElementById('cropCancelBtn');
    const cancelBtn2  = document.getElementById('cropCancelBtn2');
    const uploadForm  = document.getElementById('pfpUploadForm');
    const hiddenInput = document.getElementById('croppedImageData');

    /* ── open crop modal ── */
    function openCropModal(imageSrc) {
        cropImg.src = imageSrc;
        backdrop.classList.add('active');

        cropImg.onload = function () {
            if (cropper) cropper.destroy();
            cropper = new Cropper(cropImg, {
                aspectRatio          : 1,
                viewMode             : 1,
                dragMode             : 'move',
                autoCropArea         : 0.9,
                restore              : false,
                guides               : true,
                center               : true,
                highlight            : false,
                cropBoxMovable       : false,
                cropBoxResizable     : false,
                toggleDragModeOnDblclick: false,
            });
        };
    }

    /* ── close crop modal ── */
    function closeCropModal() {
        backdrop.classList.remove('active');
        if (cropper) { cropper.destroy(); cropper = null; }
        fileInput.value = '';
        cropImg.src = '';
    }

    /* ── file selected ── */
    fileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;

        // Type check
        if (!file.type.startsWith('image/')) {
            showUploadError({
                title   : 'Invalid File Type',
                body    : 'Your profile photo must be an image file (JPG, PNG, WEBP, etc.).',
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
                body    : `Your photo is ${sizeMB} MB, which exceeds the ${MAX_MB} MB limit. Please choose a smaller image.`,
                meta    : `Max size: ${MAX_MB} MB`,
                onRetry : () => fileInput.click(),
            });
            fileInput.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = e => openCropModal(e.target.result);
        reader.readAsDataURL(file);
    });

    /* ── save cropped image ── */
    saveBtn.addEventListener('click', function () {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({
            width                 : 400,
            height                : 400,
            imageSmoothingEnabled : true,
            imageSmoothingQuality : 'high',
        });
        hiddenInput.value = canvas.toDataURL('image/jpeg', 0.92);
        uploadForm.submit();
    });

    /* ── cancel ── */
    cancelBtn1.addEventListener('click', closeCropModal);
    cancelBtn2.addEventListener('click', closeCropModal);
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) closeCropModal();
    });

})();