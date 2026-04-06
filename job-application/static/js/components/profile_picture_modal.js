(function () {
    let cropper = null;

    const fileInput   = document.getElementById('pfpFileInput');
    const backdrop    = document.getElementById('cropModalBackdrop');
    const cropImg     = document.getElementById('cropImage');
    const saveBtn     = document.getElementById('cropSaveBtn');
    const cancelBtn1  = document.getElementById('cropCancelBtn');
    const cancelBtn2  = document.getElementById('cropCancelBtn2');
    const uploadForm  = document.getElementById('pfpUploadForm');
    const hiddenInput = document.getElementById('croppedImageData');

    function openCropModal(imageSrc) {
        cropImg.src = imageSrc;
        backdrop.classList.add('active');
        cropImg.onload = function () {
            if (cropper) cropper.destroy();
            cropper = new Cropper(cropImg, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.9,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: false,
                cropBoxResizable: false,
                toggleDragModeOnDblclick: false,
            });
        };
    }

    function closeCropModal() {
        backdrop.classList.remove('active');
        if (cropper) { cropper.destroy(); cropper = null; }
        fileInput.value = '';
        cropImg.src = '';
    }

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
        reader.onload = e => openCropModal(e.target.result);
        reader.readAsDataURL(file);
    });

    saveBtn.addEventListener('click', function () {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({
            width: 400,
            height: 400,
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high',
        });
        hiddenInput.value = canvas.toDataURL('image/jpeg', 0.92);
        uploadForm.submit();
    });

    cancelBtn1.addEventListener('click', closeCropModal);
    cancelBtn2.addEventListener('click', closeCropModal);
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) closeCropModal();
    });
})();