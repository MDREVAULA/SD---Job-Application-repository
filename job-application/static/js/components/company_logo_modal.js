(function () {
    let logoCropper = null;

    const fileInput   = document.getElementById('logoFileInput');
    const backdrop    = document.getElementById('logoCropBackdrop');
    const cropImg     = document.getElementById('logoCropImage');
    const saveBtn     = document.getElementById('logoCropSaveBtn');
    const cancelBtn1  = document.getElementById('logoCancelBtn1');
    const cancelBtn2  = document.getElementById('logoCancelBtn2');
    const uploadForm  = document.getElementById('logoUploadForm');
    const hiddenInput = document.getElementById('logoCroppedData');

    // Ensure modal is hidden on script load (before DOMContentLoaded fires)
    if (backdrop) {
        backdrop.style.display = 'none';
    }

    function openModal(src) {
        cropImg.src = src;
        backdrop.style.display = 'flex';
        // Small delay so display:flex is painted before adding active (for CSS transitions)
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                backdrop.classList.add('active');
            });
        });
        cropImg.onload = function () {
            if (logoCropper) logoCropper.destroy();
            logoCropper = new Cropper(cropImg, {
                aspectRatio: NaN,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.9,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
            });
        };
    }

    function closeModal() {
        backdrop.classList.remove('active');
        // Wait for CSS transition before hiding
        setTimeout(() => {
            backdrop.style.display = 'none';
        }, 250);
        if (logoCropper) { logoCropper.destroy(); logoCropper = null; }
        fileInput.value = '';
        cropImg.src = '';
    }

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file.');
                fileInput.value = '';
                return;
            }
            if (file.size > 10 * 1024 * 1024) {
                alert('Image must be under 10MB.');
                fileInput.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = e => openModal(e.target.result);
            reader.readAsDataURL(file);
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            if (!logoCropper) return;

            const canvas = logoCropper.getCroppedCanvas({
                maxWidth: 800,
                maxHeight: 800,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
            });

            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const hasTransparency = Array.from(imageData.data)
                .some((val, idx) => idx % 4 === 3 && val < 255);

            hiddenInput.value = hasTransparency
                ? canvas.toDataURL('image/png')
                : canvas.toDataURL('image/jpeg', 0.85);

            uploadForm.submit();
        });
    }

    if (cancelBtn1) cancelBtn1.addEventListener('click', closeModal);
    if (cancelBtn2) cancelBtn2.addEventListener('click', closeModal);
    if (backdrop) {
        backdrop.addEventListener('click', e => {
            if (e.target === backdrop) closeModal();
        });
    }
})();