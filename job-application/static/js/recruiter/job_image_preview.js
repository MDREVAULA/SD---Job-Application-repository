/**
 * job_image_preview.js
 *
 * Handles:
 *  - Cover photo selection with CROP / ADJUST modal before committing
 *  - Gallery image previews with per-file size validation
 *  - Work arrangement tag toggling
 *  - Drag-and-drop for both cover and gallery
 *
 * File size limits:
 *  - Cover photo : MAX_COVER_MB  (default 5 MB)
 *  - Gallery     : MAX_GALLERY_MB (default 10 MB)
 */

document.addEventListener("DOMContentLoaded", function () {

  /* ═══════════════════════════════════════════════════════════════
     CONSTANTS
  ═══════════════════════════════════════════════════════════════ */
  const MAX_COVER_MB   = 5;
  const MAX_GALLERY_MB = 10;
  const MAX_COVER_BYTES   = MAX_COVER_MB   * 1024 * 1024;
  const MAX_GALLERY_BYTES = MAX_GALLERY_MB * 1024 * 1024;

  /* ═══════════════════════════════════════════════════════════════
     UTILITY HELPERS
  ═══════════════════════════════════════════════════════════════ */

  /**
   * Show a styled inline error below a given element.
   * Clears itself after `durationMs` (default 6 s) or when dismissed.
   */
  function showFileError(anchorEl, message, durationMs) {
    durationMs = durationMs || 6000;

    // Remove any existing error bubble near this anchor
    const existing = anchorEl.parentNode.querySelector(".file-error-bubble");
    if (existing) existing.remove();

    const bubble = document.createElement("div");
    bubble.className = "file-error-bubble";
    bubble.innerHTML =
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:1px">' +
        '<circle cx="12" cy="12" r="10"/>' +
        '<line x1="12" y1="8" x2="12" y2="12"/>' +
        '<line x1="12" y1="16" x2="12.01" y2="16"/>' +
      "</svg>" +
      '<span style="flex:1">' + message + "</span>" +
      '<button type="button" class="file-error-dismiss" aria-label="Dismiss">×</button>';

    bubble.style.cssText = [
      "display:flex",
      "align-items:flex-start",
      "gap:8px",
      "margin-top:10px",
      "padding:10px 14px",
      "background:#fef2f2",
      "border:1px solid #fca5a5",
      "border-left:4px solid #ef4444",
      "border-radius:8px",
      "font-size:13px",
      "color:#b91c1c",
      "animation:fileErrIn 0.25s ease",
    ].join(";");

    bubble.querySelector(".file-error-dismiss").style.cssText =
      "background:none;border:none;cursor:pointer;font-size:18px;line-height:1;" +
      "color:#b91c1c;padding:0 0 0 4px;flex-shrink:0;";

    bubble.querySelector(".file-error-dismiss").addEventListener("click", function () {
      bubble.remove();
    });

    // Insert right after the anchor element
    anchorEl.parentNode.insertBefore(bubble, anchorEl.nextSibling);

    // Auto-dismiss
    setTimeout(function () {
      if (bubble.parentNode) {
        bubble.style.opacity = "0";
        bubble.style.transition = "opacity 0.3s ease";
        setTimeout(function () { bubble.remove(); }, 300);
      }
    }, durationMs);

    return bubble;
  }

  /** Format bytes to a human-readable string */
  function formatBytes(bytes) {
    if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    if (bytes >= 1024)        return (bytes / 1024).toFixed(0) + " KB";
    return bytes + " B";
  }

  /** Inject the animation keyframe once */
  if (!document.getElementById("_fileErrKeyframe")) {
    const style = document.createElement("style");
    style.id = "_fileErrKeyframe";
    style.textContent =
      "@keyframes fileErrIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}";
    document.head.appendChild(style);
  }


  /* ═══════════════════════════════════════════════════════════════
     COVER PHOTO — CROP / ADJUST MODAL
  ═══════════════════════════════════════════════════════════════ */

  /**
   * Build a lightweight crop-and-preview modal so the user can
   * pan / zoom the selected image before it is committed to the
   * <input> and the page preview.
   *
   * Returns the modal element (already appended to <body>).
   */
  function buildCropModal() {
    if (document.getElementById("_coverCropModal")) {
      return document.getElementById("_coverCropModal");
    }

    // Inject modal styles
    const style = document.createElement("style");
    style.textContent = `
      #_coverCropModal {
        display:none; position:fixed; inset:0; z-index:9999;
        background:rgba(0,0,0,0.72); backdrop-filter:blur(4px);
        align-items:center; justify-content:center; padding:16px;
      }
      #_coverCropModal.open { display:flex; }
      ._crop-box {
        background:var(--bg-secondary,#fff); border-radius:16px;
        width:min(680px,100%); box-shadow:0 24px 60px rgba(0,0,0,0.4);
        overflow:hidden; display:flex; flex-direction:column;
      }
      ._crop-header {
        display:flex; align-items:center; justify-content:space-between;
        padding:18px 24px; border-bottom:1px solid var(--border-color,#e5e7eb);
      }
      ._crop-header h3 {
        margin:0; font-size:16px; font-weight:600;
        color:var(--text-primary,#111);
      }
      ._crop-close {
        background:none; border:none; cursor:pointer; font-size:22px;
        line-height:1; color:var(--text-muted,#9ca3af); padding:2px 6px;
        border-radius:6px; transition:background 0.15s;
      }
      ._crop-close:hover { background:var(--bg-hover,#f3f4f6); color:var(--text-primary,#111); }
      ._crop-viewport {
        position:relative; width:100%; height:260px;
        overflow:hidden; background:#000; cursor:grab;
        user-select:none; touch-action:none;
      }
      ._crop-viewport.grabbing { cursor:grabbing; }
      ._crop-img {
        position:absolute; transform-origin:0 0;
        will-change:transform; pointer-events:none;
      }
      /* rule-of-thirds grid overlay */
      ._crop-grid {
        position:absolute; inset:0; pointer-events:none;
        background:
          repeating-linear-gradient(
            to right,
            rgba(255,255,255,0.18) 0, rgba(255,255,255,0.18) 1px,
            transparent 1px, transparent 33.33%
          ),
          repeating-linear-gradient(
            to bottom,
            rgba(255,255,255,0.18) 0, rgba(255,255,255,0.18) 1px,
            transparent 1px, transparent 33.33%
          );
      }
      ._crop-controls {
        padding:16px 24px; display:flex; flex-direction:column; gap:12px;
        background:var(--bg-surface-alt,#f9fafb);
        border-top:1px solid var(--border-color,#e5e7eb);
      }
      ._crop-zoom-row {
        display:flex; align-items:center; gap:12px;
      }
      ._crop-zoom-label {
        font-size:12px; font-weight:500; color:var(--text-muted,#9ca3af);
        white-space:nowrap; min-width:44px;
      }
      ._crop-zoom-slider {
        flex:1; accent-color:#14b8a6; cursor:pointer;
      }
      ._crop-hint {
        font-size:12px; color:var(--text-muted,#9ca3af);
        display:flex; align-items:center; gap:6px;
      }
      ._crop-hint svg { flex-shrink:0; }
      ._crop-actions {
        display:flex; gap:10px; padding:16px 24px;
        border-top:1px solid var(--border-color,#e5e7eb);
        background:var(--bg-secondary,#fff);
      }
      ._crop-btn-cancel {
        flex:1; padding:10px; border-radius:8px;
        border:1px solid var(--border-color,#e5e7eb);
        background:var(--bg-surface,#f9fafb); color:var(--text-primary,#111);
        font-size:14px; font-weight:500; cursor:pointer; transition:background 0.15s;
      }
      ._crop-btn-cancel:hover { background:var(--bg-hover,#f3f4f6); }
      ._crop-btn-apply {
        flex:2; padding:10px; border-radius:8px;
        border:none; background:#14b8a6; color:#fff;
        font-size:14px; font-weight:600; cursor:pointer; transition:background 0.15s;
      }
      ._crop-btn-apply:hover { background:#0f9488; }

      /* file-info strip */
      ._crop-file-info {
        padding:10px 24px 0;
        font-size:12px; color:var(--text-muted,#9ca3af);
        display:flex; align-items:center; gap:6px;
      }
    `;
    document.head.appendChild(style);

    const modal = document.createElement("div");
    modal.id = "_coverCropModal";
    modal.innerHTML = `
      <div class="_crop-box">
        <div class="_crop-header">
          <h3>Adjust Cover Photo</h3>
          <button type="button" class="_crop-close" id="_cropCloseBtn" aria-label="Close">×</button>
        </div>
        <div class="_crop-file-info" id="_cropFileInfo"></div>
        <div class="_crop-viewport" id="_cropViewport">
          <img class="_crop-img" id="_cropImg" alt="Cover preview">
          <div class="_crop-grid"></div>
        </div>
        <div class="_crop-controls">
          <div class="_crop-zoom-row">
            <span class="_crop-zoom-label">Zoom</span>
            <input type="range" class="_crop-zoom-slider" id="_cropZoom"
              min="1" max="3" step="0.01" value="1">
            <span class="_crop-zoom-label" id="_cropZoomVal" style="text-align:right">100 %</span>
          </div>
          <div class="_crop-hint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Drag the image to reposition • Use the slider to zoom in or out
          </div>
        </div>
        <div class="_crop-actions">
          <button type="button" class="_crop-btn-cancel" id="_cropCancelBtn">Cancel</button>
          <button type="button" class="_crop-btn-apply" id="_cropApplyBtn">
            Use This Photo
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    return modal;
  }

  /**
   * Open the crop modal for a given File object.
   * Calls `onApply(file, objectURL)` when the user confirms.
   * Calls `onCancel()` when dismissed.
   */
  function openCropModal(file, onApply, onCancel) {
    const modal    = buildCropModal();
    const viewport = document.getElementById("_cropViewport");
    const img      = document.getElementById("_cropImg");
    const zoom     = document.getElementById("_cropZoom");
    const zoomVal  = document.getElementById("_cropZoomVal");
    const fileInfo = document.getElementById("_cropFileInfo");

    // Show file metadata
    fileInfo.textContent =
      file.name + "  ·  " + formatBytes(file.size) +
      "  ·  Recommended: 1200 × 400 px";

    // Load the image
    const objectURL = URL.createObjectURL(file);
    img.onload = function () {
      resetTransform();
    };
    img.src = objectURL;

    // State
    let scale   = 1;
    let offsetX = 0;
    let offsetY = 0;
    let dragging = false;
    let startX, startY, startOffX, startOffY;

    zoom.value = "1";
    zoomVal.textContent = "100 %";

    function clampOffset() {
      const vw = viewport.clientWidth;
      const vh = viewport.clientHeight;
      const iw = img.naturalWidth  * scale;
      const ih = img.naturalHeight * scale;
      const minX = Math.min(0, vw - iw);
      const minY = Math.min(0, vh - ih);
      offsetX = Math.max(minX, Math.min(0, offsetX));
      offsetY = Math.max(minY, Math.min(0, offsetY));
    }

    function applyTransform() {
      img.style.transform = "translate(" + offsetX + "px," + offsetY + "px) scale(" + scale + ")";
    }

    function resetTransform() {
      const vw = viewport.clientWidth;
      const vh = viewport.clientHeight;
      const iw = img.naturalWidth;
      const ih = img.naturalHeight;
      // Fit to width by default
      scale   = Math.max(vw / iw, vh / ih);
      zoom.min   = scale.toFixed(3);
      zoom.max   = (scale * 3).toFixed(3);
      zoom.step  = (scale * 0.01).toFixed(4);
      zoom.value = scale.toFixed(3);
      zoomVal.textContent = "100 %";
      offsetX = (vw - iw * scale) / 2;
      offsetY = (vh - ih * scale) / 2;
      applyTransform();
    }

    // Zoom slider
    zoom.oninput = function () {
      const newScale = parseFloat(this.value);
      const baseScale = parseFloat(zoom.min);
      zoomVal.textContent = Math.round((newScale / baseScale) * 100) + " %";
      // Zoom around center
      const cx = viewport.clientWidth  / 2;
      const cy = viewport.clientHeight / 2;
      offsetX = cx - (cx - offsetX) * (newScale / scale);
      offsetY = cy - (cy - offsetY) * (newScale / scale);
      scale   = newScale;
      clampOffset();
      applyTransform();
    };

    // Drag (mouse)
    viewport.addEventListener("mousedown", onMouseDown);
    function onMouseDown(e) {
      dragging = true;
      startX = e.clientX; startY = e.clientY;
      startOffX = offsetX; startOffY = offsetY;
      viewport.classList.add("grabbing");
      e.preventDefault();
    }
    function onMouseMove(e) {
      if (!dragging) return;
      offsetX = startOffX + (e.clientX - startX);
      offsetY = startOffY + (e.clientY - startY);
      clampOffset();
      applyTransform();
    }
    function onMouseUp() {
      dragging = false;
      viewport.classList.remove("grabbing");
    }
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup",   onMouseUp);

    // Drag (touch)
    viewport.addEventListener("touchstart", onTouchStart, { passive: true });
    function onTouchStart(e) {
      if (e.touches.length !== 1) return;
      dragging = true;
      startX = e.touches[0].clientX; startY = e.touches[0].clientY;
      startOffX = offsetX; startOffY = offsetY;
    }
    function onTouchMove(e) {
      if (!dragging || e.touches.length !== 1) return;
      offsetX = startOffX + (e.touches[0].clientX - startX);
      offsetY = startOffY + (e.touches[0].clientY - startY);
      clampOffset();
      applyTransform();
      e.preventDefault();
    }
    function onTouchEnd() { dragging = false; }
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("touchend",  onTouchEnd);

    // Open modal
    modal.classList.add("open");
    document.body.style.overflow = "hidden";

    function cleanup() {
      modal.classList.remove("open");
      document.body.style.overflow = "";
      viewport.removeEventListener("mousedown",  onMouseDown);
      document.removeEventListener("mousemove",  onMouseMove);
      document.removeEventListener("mouseup",    onMouseUp);
      viewport.removeEventListener("touchstart", onTouchStart);
      document.removeEventListener("touchmove",  onTouchMove);
      document.removeEventListener("touchend",   onTouchEnd);
      document.getElementById("_cropCancelBtn").onclick = null;
      document.getElementById("_cropApplyBtn").onclick  = null;
      document.getElementById("_cropCloseBtn").onclick  = null;
    }

    document.getElementById("_cropApplyBtn").onclick = function () {
      cleanup();
      if (typeof onApply === "function") onApply(file, objectURL);
    };

    function dismiss() {
      cleanup();
      URL.revokeObjectURL(objectURL);
      if (typeof onCancel === "function") onCancel();
    }

    document.getElementById("_cropCancelBtn").onclick = dismiss;
    document.getElementById("_cropCloseBtn").onclick  = dismiss;

    // Click outside to close
    modal.addEventListener("click", function handler(e) {
      if (e.target === modal) {
        dismiss();
        modal.removeEventListener("click", handler);
      }
    });

    // Esc key
    function onKey(e) {
      if (e.key === "Escape") {
        dismiss();
        document.removeEventListener("keydown", onKey);
      }
    }
    document.addEventListener("keydown", onKey);
  }


  /* ═══════════════════════════════════════════════════════════════
     COVER PHOTO — wiring
  ═══════════════════════════════════════════════════════════════ */

  const coverInput   = document.getElementById("coverPhotoInput") ||
                       document.getElementById("headerImageInput");
  const coverPreview = document.getElementById("coverPhotoPreview") ||
                       document.getElementById("headerPreview");

  // The anchor we'll attach error bubbles to (file-info hint paragraph)
  const coverHint =
    coverInput && coverInput.parentNode
      ? coverInput.parentNode.querySelector(".field-hint")
      : null;

  if (coverInput && coverPreview) {
    coverInput.addEventListener("change", function () {
      const file = this.files && this.files[0];
      if (!file) return;

      // ── Size check ──
      if (file.size > MAX_COVER_BYTES) {
        showFileError(
          coverHint || coverPreview,
          "Cover photo is too large (" + formatBytes(file.size) + "). " +
          "Maximum allowed size is " + MAX_COVER_MB + " MB. " +
          "Please choose a smaller image."
        );
        // Reset so the same file can be re-selected after compression
        this.value = "";
        return;
      }

      // ── Open crop modal ──
      openCropModal(
        file,
        /* onApply */ function (confirmedFile, objectURL) {
          // Update the visible preview
          coverPreview.src = objectURL;

          // Keep the <input> pointing at the confirmed file
          const dt = new DataTransfer();
          dt.items.add(confirmedFile);
          coverInput.files = dt.files;

          // Signal unsaved changes if edit_job.js exposes markDirty
          if (typeof markDirty === "function") markDirty();
        },
        /* onCancel */ function () {
          // Clear the input so re-selecting the same file triggers change again
          coverInput.value = "";
        }
      );
    });
  }


  /* ═══════════════════════════════════════════════════════════════
     GALLERY IMAGES — preview with per-file validation
  ═══════════════════════════════════════════════════════════════ */

  const fileInput        = document.getElementById("posterInput");
  const previewContainer = document.getElementById("imagePreviewContainer");

  let selectedFiles = [];

  // Anchor for gallery errors
  const galleryUploadZone = document.querySelector(".upload-zone");

  if (fileInput && previewContainer) {
    fileInput.addEventListener("change", function () {
      const newFiles   = Array.from(this.files);
      const oversized  = [];
      const validFiles = [];

      newFiles.forEach(function (file) {
        if (file.size > MAX_GALLERY_BYTES) {
          oversized.push(file.name + " (" + formatBytes(file.size) + ")");
        } else {
          validFiles.push(file);
        }
      });

      // ── Report oversized files ──
      if (oversized.length > 0) {
        const anchor = galleryUploadZone || previewContainer;
        const names  = oversized.map(function (n) { return "<strong>" + n + "</strong>"; }).join(", ");
        showFileError(
          anchor,
          oversized.length === 1
            ? names + " exceeds the " + MAX_GALLERY_MB + " MB limit and was not added."
            : "The following files exceed the " + MAX_GALLERY_MB + " MB limit and were skipped: " + names
        );
      }

      // ── Process valid files ──
      validFiles.forEach(function (file) {
        selectedFiles.push(file);

        const reader = new FileReader();
        reader.onload = function (e) {
          const card = document.createElement("div");
          card.classList.add("gallery-card");

          const img = document.createElement("img");
          img.src = e.target.result;
          img.classList.add("gallery-img");

          // Small file-size badge
          const badge = document.createElement("div");
          badge.style.cssText =
            "position:absolute;bottom:6px;left:6px;background:rgba(0,0,0,0.55);" +
            "color:#fff;font-size:10px;padding:2px 6px;border-radius:4px;pointer-events:none;";
          badge.textContent = formatBytes(file.size);

          const removeBtn = document.createElement("button");
          removeBtn.classList.add("gallery-remove-btn");
          removeBtn.type    = "button";
          removeBtn.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none"' +
            ' stroke="currentColor" stroke-width="2">' +
            "<line x1=\"18\" y1=\"6\" x2=\"6\" y2=\"18\"/>" +
            "<line x1=\"6\" y1=\"6\" x2=\"18\" y2=\"18\"/></svg>";

          removeBtn.onclick = function () {
            const index = selectedFiles.indexOf(file);
            if (index > -1) selectedFiles.splice(index, 1);
            card.remove();
            syncFileInput();
          };

          card.appendChild(img);
          card.appendChild(badge);
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
    selectedFiles.forEach(function (f) { dt.items.add(f); });
    if (fileInput) fileInput.files = dt.files;
  }


  /* ═══════════════════════════════════════════════════════════════
     WORK ARRANGEMENT TAGS
  ═══════════════════════════════════════════════════════════════ */

  const arrangementContainer = document.getElementById("arrangementTags");
  const arrangementInput     = document.getElementById("arrangementInput");

  if (arrangementContainer && arrangementInput) {
    function syncArrangement() {
      const selected = Array.from(
        arrangementContainer.querySelectorAll(".tag.sel")
      ).map(function (t) { return t.dataset.val; });
      arrangementInput.value = selected.join(", ");
    }

    arrangementContainer.querySelectorAll(".tag").forEach(function (tag) {
      tag.addEventListener("click", function () {
        tag.classList.toggle("sel");
        syncArrangement();
        if (typeof markDirty === "function") markDirty();
      });
    });

    // Reflect pre-selected tags on load (edit mode)
    syncArrangement();
  }


  /* ═══════════════════════════════════════════════════════════════
     DRAG & DROP — gallery upload zone
  ═══════════════════════════════════════════════════════════════ */

  const uploadZone = document.querySelector(".upload-zone");
  if (uploadZone && fileInput) {
    uploadZone.addEventListener("dragover", function (e) {
      e.preventDefault();
      uploadZone.classList.add("drag-over");
    });
    uploadZone.addEventListener("dragleave", function () {
      uploadZone.classList.remove("drag-over");
    });
    uploadZone.addEventListener("drop", function (e) {
      e.preventDefault();
      uploadZone.classList.remove("drag-over");

      const dropped = Array.from(e.dataTransfer.files);
      dropped.forEach(function (file) { selectedFiles.push(file); });
      syncFileInput();
      // Trigger change so previews are rendered + validation runs
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }


  /* ═══════════════════════════════════════════════════════════════
     DRAG & DROP — cover photo container
  ═══════════════════════════════════════════════════════════════ */

  const coverContainer = document.getElementById("coverPhotoContainer");
  if (coverContainer && coverInput) {
    coverContainer.addEventListener("dragover", function (e) {
      e.preventDefault();
      coverContainer.style.outline = "2px dashed #14b8a6";
    });
    coverContainer.addEventListener("dragleave", function () {
      coverContainer.style.outline = "";
    });
    coverContainer.addEventListener("drop", function (e) {
      e.preventDefault();
      coverContainer.style.outline = "";

      if (e.dataTransfer.files.length) {
        const file = e.dataTransfer.files[0];

        // Size check before opening modal
        if (file.size > MAX_COVER_BYTES) {
          showFileError(
            coverHint || coverPreview,
            "Cover photo is too large (" + formatBytes(file.size) + "). " +
            "Maximum allowed size is " + MAX_COVER_MB + " MB."
          );
          return;
        }

        const dt = new DataTransfer();
        dt.items.add(file);
        coverInput.files = dt.files;
        // Fire change to open the crop modal
        coverInput.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  }

}); // end DOMContentLoaded