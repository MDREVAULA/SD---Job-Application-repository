document.addEventListener("DOMContentLoaded", function () {

  // ===================================
  // IMAGE PREVIEW (gallery / poster)
  // ===================================
  const fileInput        = document.getElementById("posterInput");
  const previewContainer = document.getElementById("imagePreviewContainer");

  let selectedFiles = [];

  if (fileInput && previewContainer) {
    fileInput.addEventListener("change", function () {
      const newFiles = Array.from(this.files);

      newFiles.forEach(file => {
        selectedFiles.push(file);

        const reader = new FileReader();
        reader.onload = function (e) {
          const card = document.createElement("div");
          card.classList.add("gallery-card");          // matches gallery CSS

          const img = document.createElement("img");
          img.src = e.target.result;
          img.classList.add("gallery-img");

          const removeBtn = document.createElement("button");
          removeBtn.classList.add("gallery-remove-btn");
          removeBtn.type = "button";
          removeBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>`;

          removeBtn.onclick = function () {
            const index = selectedFiles.indexOf(file);
            if (index > -1) selectedFiles.splice(index, 1);
            card.remove();
            syncFileInput();
          };

          card.appendChild(img);
          card.appendChild(removeBtn);
          previewContainer.appendChild(card);
        };
        reader.readAsDataURL(file);
      });

      syncFileInput();
    });
  }

  function syncFileInput() {
    const dt = new DataTransfer();
    selectedFiles.forEach(f => dt.items.add(f));
    if (fileInput) fileInput.files = dt.files;
  }

  // ===================================
  // COVER PHOTO PREVIEW
  // Supports both id="coverPhotoInput" (edit_job)
  // and id="headerImageInput" (post_job)
  // ===================================
  const coverInput  = document.getElementById("coverPhotoInput")  ||
                      document.getElementById("headerImageInput");
  const coverPreview = document.getElementById("coverPhotoPreview") ||
                       document.getElementById("headerPreview");

  if (coverInput && coverPreview) {
    coverInput.addEventListener("change", function () {
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => { coverPreview.src = e.target.result; };
        reader.readAsDataURL(this.files[0]);
      }
    });
  }

  // ===================================
  // WORK ARRANGEMENT TAGS
  // Works for both post_job and edit_job
  // ===================================
  const arrangementContainer = document.getElementById("arrangementTags");
  const arrangementInput     = document.getElementById("arrangementInput");

  if (arrangementContainer && arrangementInput) {
    function syncArrangement() {
      const selected = Array.from(
        arrangementContainer.querySelectorAll(".tag.sel")
      ).map(t => t.dataset.val);
      arrangementInput.value = selected.join(", ");
    }

    arrangementContainer.querySelectorAll(".tag").forEach(tag => {
      tag.addEventListener("click", () => {
        tag.classList.toggle("sel");
        syncArrangement();
      });
    });

    // Run once on load so hidden input reflects pre-selected tags (edit mode)
    syncArrangement();
  }

  // ===================================
  // DRAG & DROP — gallery upload zone
  // ===================================
  const uploadZone = document.querySelector(".upload-zone");
  if (uploadZone && fileInput) {
    uploadZone.addEventListener("dragover", e => {
      e.preventDefault();
      uploadZone.classList.add("drag-over");
    });
    uploadZone.addEventListener("dragleave", () =>
      uploadZone.classList.remove("drag-over")
    );
    uploadZone.addEventListener("drop", e => {
      e.preventDefault();
      uploadZone.classList.remove("drag-over");
      // Merge dropped files with already-selected files
      const dropped = Array.from(e.dataTransfer.files);
      dropped.forEach(file => selectedFiles.push(file));
      syncFileInput();
      // Trigger change event so previews render
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  // ===================================
  // DRAG & DROP — cover photo container
  // ===================================
  const coverContainer = document.getElementById("coverPhotoContainer");
  if (coverContainer && coverInput) {
    coverContainer.addEventListener("dragover", e => {
      e.preventDefault();
      coverContainer.style.outline = "2px dashed #14b8a6";
    });
    coverContainer.addEventListener("dragleave", () => {
      coverContainer.style.outline = "";
    });
    coverContainer.addEventListener("drop", e => {
      e.preventDefault();
      coverContainer.style.outline = "";
      if (e.dataTransfer.files.length) {
        const dt = new DataTransfer();
        dt.items.add(e.dataTransfer.files[0]);
        coverInput.files = dt.files;
        coverInput.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  }

});