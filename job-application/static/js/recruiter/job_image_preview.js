document.addEventListener("DOMContentLoaded", function () {
 
  /* ─── constants ─────────────────────────────────────────────── */
  var MAX_COVER_MB      = 5;
  var MAX_GALLERY_MB    = 10;
  var MAX_COVER_BYTES   = MAX_COVER_MB   * 1024 * 1024;
  var MAX_GALLERY_BYTES = MAX_GALLERY_MB * 1024 * 1024;
 
  /* Canvas output size — matches the recommended cover photo spec */
  var OUTPUT_W = 1200;
  var OUTPUT_H = 400;
 
  /* ─── stabilise existing cover images to prevent load-flash ─── */
  document.querySelectorAll(
    "#coverPhotoPreview, #headerPreview, .header-image-container .header-img"
  ).forEach(function (img) {
    img.style.cssText +=
      ";width:100%;height:100%;object-fit:cover;display:block;" +
      "background:var(--bg-surface-alt,#f3f4f6);";
  });
 
  /* ─── utility helpers ───────────────────────────────────────── */
  function formatBytes(bytes) {
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
    if (bytes >= 1024)    return (bytes / 1024).toFixed(0)    + " KB";
    return bytes + " B";
  }
 
  function showFileError(anchorEl, message, durationMs) {
    durationMs = durationMs || 6000;
    var old = anchorEl.parentNode.querySelector(".file-error-bubble");
    if (old) old.remove();
    var bubble = document.createElement("div");
    bubble.className = "file-error-bubble";
    bubble.innerHTML =
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"' +
      ' style="flex-shrink:0;margin-top:1px"><circle cx="12" cy="12" r="10"/>' +
      '<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' +
      '<span style="flex:1">' + message + "</span>" +
      '<button type="button" class="file-error-dismiss" aria-label="Dismiss">\xd7</button>';
    bubble.style.cssText =
      "display:flex;align-items:flex-start;gap:8px;margin-top:10px;" +
      "padding:10px 14px;background:#fef2f2;border:1px solid #fca5a5;" +
      "border-left:4px solid #ef4444;border-radius:8px;font-size:13px;" +
      "color:#b91c1c;animation:_feIn 0.25s ease;";
    bubble.querySelector(".file-error-dismiss").style.cssText =
      "background:none;border:none;cursor:pointer;font-size:18px;" +
      "line-height:1;color:#b91c1c;padding:0 0 0 4px;flex-shrink:0;";
    bubble.querySelector(".file-error-dismiss").onclick = function () { bubble.remove(); };
    anchorEl.parentNode.insertBefore(bubble, anchorEl.nextSibling);
    setTimeout(function () {
      if (bubble.parentNode) {
        bubble.style.opacity = "0";
        bubble.style.transition = "opacity 0.3s";
        setTimeout(function () { bubble.remove(); }, 300);
      }
    }, durationMs);
  }
 
  if (!document.getElementById("_feStyle")) {
    var s = document.createElement("style");
    s.id = "_feStyle";
    s.textContent =
      "@keyframes _feIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}";
    document.head.appendChild(s);
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     CANVAS CROP EXPORT
     Translates the current pan/zoom state into a real cropped
     JPEG blob at OUTPUT_W × OUTPUT_H pixels.
  ═══════════════════════════════════════════════════════════ */
  function exportCrop(imgEl, viewport, scale, offsetX, offsetY, mimeType, callback) {
    var vw = viewport.clientWidth;
    var vh = viewport.clientWidth * (OUTPUT_H / OUTPUT_W);
 
    /*
     * The image is positioned inside the modal as:
     *   top-left corner = (offsetX, offsetY)  in modal CSS pixels
     *   rendered size   = naturalWidth * scale  ×  naturalHeight * scale
     *
     * The portion of the *source image* (in natural pixels) that is
     * currently visible through the viewport is therefore:
     *
     *   srcX = -offsetX / scale      (left edge of visible region)
     *   srcY = -offsetY / scale      (top  edge of visible region)
     *   srcW =  vw      / scale      (visible width  in image pixels)
     *   srcH =  vh      / scale      (visible height in image pixels)
     *
     * We draw exactly that rectangle onto the canvas.
     */
    var srcX = -offsetX / scale;
    var srcY = -offsetY / scale;
    var srcW =  vw      / scale;
    var srcH =  vh      / scale;
 
    /* Safety clamp (clampOffset() prevents this in normal use) */
    srcX = Math.max(0, Math.min(imgEl.naturalWidth  - srcW, srcX));
    srcY = Math.max(0, Math.min(imgEl.naturalHeight - srcH, srcY));
 
    var canvas  = document.createElement("canvas");
    canvas.width  = OUTPUT_W;
    canvas.height = OUTPUT_H;
    var ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
 
    ctx.drawImage(
      imgEl,
      srcX, srcY, srcW, srcH,       /* source rectangle  (image px) */
      0,    0,    OUTPUT_W, OUTPUT_H /* dest  rectangle  (canvas px) */
    );
 
    var exportMime = (mimeType === "image/png") ? "image/png" : "image/jpeg";
    var quality    = (exportMime === "image/jpeg") ? 0.92 : undefined;
 
    canvas.toBlob(function (blob) {
      callback(blob, URL.createObjectURL(blob));
    }, exportMime, quality);
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     CROP MODAL — build DOM once, reuse on every open
  ═══════════════════════════════════════════════════════════ */
  function buildCropModal() {
    if (document.getElementById("_coverCropModal")) {
      return document.getElementById("_coverCropModal");
    }
 
    var style = document.createElement("style");
    style.textContent = [
      "#_coverCropModal{display:none;position:fixed;inset:0;z-index:9999;",
        "background:rgba(0,0,0,0.75);backdrop-filter:blur(4px);",
        "align-items:center;justify-content:center;padding:16px;}",
      "#_coverCropModal.open{display:flex;}",
 
      "._crop-box{background:var(--bg-secondary,#1f2937);border-radius:16px;",
        "width:min(800px,calc(100vw - 32px));",
        "box-shadow:0 24px 60px rgba(0,0,0,0.55);",
        "overflow:hidden;display:flex;flex-direction:column;}",
 
      "._crop-header{display:flex;align-items:center;justify-content:space-between;",
        "padding:16px 24px;border-bottom:1px solid var(--border-color,#374151);flex-shrink:0;}",
      "._crop-header h3{margin:0;font-size:15px;font-weight:600;color:var(--text-primary,#f9fafb);}",
      "._crop-close{background:none;border:none;cursor:pointer;font-size:22px;line-height:1;",
        "color:var(--text-muted,#9ca3af);padding:2px 6px;border-radius:6px;transition:background .15s;}",
      "._crop-close:hover{background:var(--bg-hover,#374151);color:var(--text-primary,#f9fafb);}",
 
      /* The viewport uses the EXACT same aspect ratio as the cover photo */
      "._crop-viewport{position:relative;width:100%;",
        "aspect-ratio:" + OUTPUT_W + "/" + OUTPUT_H + ";",
        "overflow:hidden;background:#000;cursor:grab;user-select:none;touch-action:none;flex-shrink:0;}",
      "._crop-viewport.grabbing{cursor:grabbing;}",
      "._crop-img{position:absolute;transform-origin:0 0;will-change:transform;pointer-events:none;}",
 
      /* Rule-of-thirds grid */
      "._crop-grid{position:absolute;inset:0;pointer-events:none;",
        "background:",
          "repeating-linear-gradient(to right,rgba(255,255,255,0.1) 0,rgba(255,255,255,0.1) 1px,transparent 1px,transparent 33.33%),",
          "repeating-linear-gradient(to bottom,rgba(255,255,255,0.1) 0,rgba(255,255,255,0.1) 1px,transparent 1px,transparent 33.33%);}",
 
      /* Output size badge */
      "._crop-badge{position:absolute;bottom:10px;right:10px;",
        "background:rgba(0,0,0,0.65);color:#fff;font-size:11px;font-weight:600;",
        "letter-spacing:.04em;padding:3px 8px;border-radius:4px;pointer-events:none;z-index:5;}",
 
      "._crop-fileinfo{padding:10px 24px 0;font-size:12px;color:var(--text-muted,#9ca3af);",
        "display:flex;align-items:center;gap:6px;flex-shrink:0;}",
 
      "._crop-controls{padding:14px 24px;display:flex;flex-direction:column;gap:10px;",
        "background:var(--bg-surface-alt,#111827);border-top:1px solid var(--border-color,#374151);flex-shrink:0;}",
      "._crop-zoom-row{display:flex;align-items:center;gap:12px;}",
      "._crop-zlabel{font-size:12px;font-weight:500;color:var(--text-muted,#9ca3af);white-space:nowrap;min-width:44px;}",
      "._crop-zoom-slider{flex:1;accent-color:#14b8a6;cursor:pointer;}",
      "._crop-hint{font-size:12px;color:var(--text-muted,#6b7280);display:flex;align-items:center;gap:6px;}",
      "._crop-hint svg{flex-shrink:0;}",
 
      "._crop-actions{display:flex;gap:10px;padding:14px 24px;",
        "border-top:1px solid var(--border-color,#374151);",
        "background:var(--bg-secondary,#1f2937);flex-shrink:0;}",
      "._crop-btn-cancel{flex:1;padding:10px;border-radius:8px;",
        "border:1px solid var(--border-color,#374151);",
        "background:var(--bg-surface,#374151);color:var(--text-primary,#f9fafb);",
        "font-size:14px;font-weight:500;cursor:pointer;transition:background .15s;}",
      "._crop-btn-cancel:hover{background:var(--bg-hover,#4b5563);}",
      "._crop-btn-apply{flex:2;padding:10px;border-radius:8px;border:none;",
        "background:#14b8a6;color:#fff;font-size:14px;font-weight:600;",
        "cursor:pointer;transition:background .15s;}",
      "._crop-btn-apply:hover:not(:disabled){background:#0f9488;}",
      "._crop-btn-apply:disabled{background:#6b7280;cursor:not-allowed;}",
      "@media(max-width:480px){._crop-actions{flex-direction:column;}",
        "._crop-btn-cancel,._crop-btn-apply{flex:none;width:100%;}}"
    ].join("");
    document.head.appendChild(style);
 
    var modal = document.createElement("div");
    modal.id = "_coverCropModal";
    modal.innerHTML =
      '<div class="_crop-box">' +
        '<div class="_crop-header">' +
          '<h3>Adjust Cover Photo</h3>' +
          '<button type="button" class="_crop-close" id="_cropCloseBtn" aria-label="Close">\xd7</button>' +
        '</div>' +
        '<div class="_crop-fileinfo" id="_cropFileInfo"></div>' +
        '<div class="_crop-viewport" id="_cropViewport">' +
          '<img class="_crop-img" id="_cropImg" alt="">' +
          '<div class="_crop-grid"></div>' +
          '<div class="_crop-badge">Output: ' + OUTPUT_W + ' \xd7 ' + OUTPUT_H + ' px</div>' +
        '</div>' +
        '<div class="_crop-controls">' +
          '<div class="_crop-zoom-row">' +
            '<span class="_crop-zlabel">Zoom</span>' +
            '<input type="range" class="_crop-zoom-slider" id="_cropZoom" min="1" max="3" step="0.01" value="1">' +
            '<span class="_crop-zlabel" id="_cropZoomVal" style="text-align:right">100%</span>' +
          '</div>' +
          '<div class="_crop-hint">' +
            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
              '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/>' +
              '<line x1="12" y1="17" x2="12.01" y2="17"/>' +
            '</svg>' +
            'Drag to reposition \u2022 Slider to zoom \u2022 What you see here is exactly what will be saved' +
          '</div>' +
        '</div>' +
        '<div class="_crop-actions">' +
          '<button type="button" class="_crop-btn-cancel" id="_cropCancelBtn">Cancel</button>' +
          '<button type="button" class="_crop-btn-apply"  id="_cropApplyBtn">Use This Photo</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    return modal;
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     OPEN CROP MODAL
  ═══════════════════════════════════════════════════════════ */
  function openCropModal(originalFile, onApply, onCancel) {
    var modal    = buildCropModal();
    var viewport = document.getElementById("_cropViewport");
    var imgEl    = document.getElementById("_cropImg");
    var zoom     = document.getElementById("_cropZoom");
    var zoomVal  = document.getElementById("_cropZoomVal");
    var fileInfo = document.getElementById("_cropFileInfo");
    var applyBtn = document.getElementById("_cropApplyBtn");
 
    fileInfo.textContent =
      originalFile.name + "  \u00b7  " + formatBytes(originalFile.size) +
      "  \u00b7  Saved as: " + OUTPUT_W + " \xd7 " + OUTPUT_H + " px";
 
    var mimeType  = originalFile.type || "image/jpeg";
    if (mimeType === "image/gif") mimeType = "image/jpeg";
 
    /* State */
    var scale     = 1;
    var baseScale = 1;
    var offsetX   = 0;
    var offsetY   = 0;
    var dragging  = false;
    var startX, startY, startOffX, startOffY;
 
    function clampOffset() {
      var vw   = viewport.clientWidth;
      var vh   = viewport.clientHeight;
      var minX = Math.min(0, vw  - imgEl.naturalWidth  * scale);
      var minY = Math.min(0, vh  - imgEl.naturalHeight * scale);
      offsetX  = Math.max(minX, Math.min(0, offsetX));
      offsetY  = Math.max(minY, Math.min(0, offsetY));
    }
 
    function applyTransform() {
      imgEl.style.transform =
        "translate(" + offsetX + "px," + offsetY + "px) scale(" + scale + ")";
    }
 
    function resetTransform() {
      var vw = viewport.clientWidth;
      var vh = viewport.clientWidth * (OUTPUT_H / OUTPUT_W);
      var iw = imgEl.naturalWidth;
      var ih = imgEl.naturalHeight;
 
      /* Cover fit: scale so the image fills the viewport completely */
      baseScale = Math.max(vw / iw, vh / ih);
      scale     = baseScale;
 
      zoom.min   = baseScale.toFixed(5);
      zoom.max   = (baseScale * 3).toFixed(5);
      zoom.step  = (baseScale * 0.005).toFixed(6);
      zoom.value = baseScale.toFixed(5);
      zoomVal.textContent = "100%";
 
      /* Centre the image */
      offsetX = (vw - iw * scale) / 2;
      offsetY = (vh - ih * scale) / 2;
      clampOffset();
      applyTransform();
    }
 
    /* Load image */
    var rawURL = URL.createObjectURL(originalFile);
    applyBtn.disabled    = true;
    applyBtn.textContent = "Loading…";
    imgEl.onload = function () {
      resetTransform();
      applyBtn.disabled    = false;
      applyBtn.textContent = "Use This Photo";
    };
    imgEl.src = rawURL;
 
    /* Zoom slider */
    zoom.oninput = function () {
      var ns  = parseFloat(this.value);
      zoomVal.textContent = Math.round((ns / baseScale) * 100) + "%";
      var cx  = viewport.clientWidth  / 2;
      var cy  = viewport.clientHeight / 2;
      offsetX = cx - (cx - offsetX) * (ns / scale);
      offsetY = cy - (cy - offsetY) * (ns / scale);
      scale   = ns;
      clampOffset();
      applyTransform();
    };
 
    /* Mouse drag */
    function onMD(e) {
      dragging = true;
      startX = e.clientX; startY = e.clientY;
      startOffX = offsetX; startOffY = offsetY;
      viewport.classList.add("grabbing");
      e.preventDefault();
    }
    function onMM(e) {
      if (!dragging) return;
      offsetX = startOffX + (e.clientX - startX);
      offsetY = startOffY + (e.clientY - startY);
      clampOffset(); applyTransform();
    }
    function onMU() { dragging = false; viewport.classList.remove("grabbing"); }
    viewport.addEventListener("mousedown", onMD);
    document.addEventListener("mousemove", onMM);
    document.addEventListener("mouseup",   onMU);
 
    /* Touch drag */
    function onTS(e) {
      if (e.touches.length !== 1) return;
      dragging = true;
      startX = e.touches[0].clientX; startY = e.touches[0].clientY;
      startOffX = offsetX; startOffY = offsetY;
    }
    function onTM(e) {
      if (!dragging || e.touches.length !== 1) return;
      offsetX = startOffX + (e.touches[0].clientX - startX);
      offsetY = startOffY + (e.touches[0].clientY - startY);
      clampOffset(); applyTransform(); e.preventDefault();
    }
    function onTE() { dragging = false; }
    viewport.addEventListener("touchstart", onTS, { passive: true });
    document.addEventListener("touchmove",  onTM, { passive: false });
    document.addEventListener("touchend",   onTE);
 
    /* Open */
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
 
    function cleanup() {
      modal.classList.remove("open");
      document.body.style.overflow = "";
      viewport.removeEventListener("mousedown",  onMD);
      document.removeEventListener("mousemove",  onMM);
      document.removeEventListener("mouseup",    onMU);
      viewport.removeEventListener("touchstart", onTS);
      document.removeEventListener("touchmove",  onTM);
      document.removeEventListener("touchend",   onTE);
      document.getElementById("_cropCancelBtn").onclick = null;
      document.getElementById("_cropApplyBtn").onclick  = null;
      document.getElementById("_cropCloseBtn").onclick  = null;
      URL.revokeObjectURL(rawURL);
    }
 
    /* ── Apply: render canvas → blob → pass to caller ── */
    document.getElementById("_cropApplyBtn").onclick = function () {
      applyBtn.disabled    = true;
      applyBtn.textContent = "Processing…";
 
      exportCrop(imgEl, viewport, scale, offsetX, offsetY, mimeType,
        function (blob, croppedURL) {
          cleanup();
          if (typeof onApply === "function") onApply(blob, croppedURL);
        }
      );
    };
 
    function dismiss() {
      cleanup();
      if (typeof onCancel === "function") onCancel();
    }
    document.getElementById("_cropCancelBtn").onclick = dismiss;
    document.getElementById("_cropCloseBtn").onclick  = dismiss;
    modal.addEventListener("click", function h(e) {
      if (e.target === modal) { dismiss(); modal.removeEventListener("click", h); }
    });
    function onKey(e) {
      if (e.key === "Escape") { dismiss(); document.removeEventListener("keydown", onKey); }
    }
    document.addEventListener("keydown", onKey);
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     COVER PHOTO INPUT WIRING
  ═══════════════════════════════════════════════════════════ */
  var coverInput   = document.getElementById("coverPhotoInput") ||
                     document.getElementById("headerImageInput");
  var coverPreview = document.getElementById("coverPhotoPreview") ||
                     document.getElementById("headerPreview");
  var coverHint    = (coverInput && coverInput.parentNode)
                       ? coverInput.parentNode.querySelector(".field-hint") : null;
 
  if (coverInput && coverPreview) {
    coverInput.addEventListener("change", function () {
      var file = this.files && this.files[0];
      if (!file) return;
 
      if (file.size > MAX_COVER_BYTES) {
        showFileError(coverHint || coverPreview,
          "Cover photo is too large (" + formatBytes(file.size) + "). " +
          "Maximum allowed size is " + MAX_COVER_MB + " MB.");
        this.value = "";
        return;
      }
 
      openCropModal(file,
        /* onApply — blob IS the cropped image; no re-cropping on server */
        function (croppedBlob, croppedURL) {
          /* Lock styles BEFORE setting src → zero-frame flash */
          coverPreview.style.cssText +=
            ";width:100%;height:100%;object-fit:cover;display:block;";
          coverPreview.src = croppedURL;
 
          /* Replace file input contents with the cropped blob */
          var ext      = (croppedBlob.type === "image/png") ? ".png" : ".jpg";
          var newFile  = new File(
            [croppedBlob],
            file.name.replace(/\.[^.]+$/, "") + "_cover" + ext,
            { type: croppedBlob.type }
          );
          var dt = new DataTransfer();
          dt.items.add(newFile);
          coverInput.files = dt.files;
 
          if (typeof markDirty === "function") markDirty();
        },
        /* onCancel */
        function () { coverInput.value = ""; }
      );
    });
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     GALLERY IMAGES
  ═══════════════════════════════════════════════════════════ */
  var fileInput        = document.getElementById("posterInput");
  var previewContainer = document.getElementById("imagePreviewContainer");
  var selectedFiles    = [];
  var galleryZone      = document.querySelector(".upload-zone");
 
  if (fileInput && previewContainer) {
    fileInput.addEventListener("change", function () {
      var newFiles  = Array.from(this.files);
      var oversized = [];
      var valid     = [];
 
      newFiles.forEach(function (f) {
        (f.size > MAX_GALLERY_BYTES ? oversized : valid).push(f);
      });
 
      if (oversized.length) {
        var anchor = galleryZone || previewContainer;
        var names  = oversized.map(function (f) {
          return "<strong>" + f.name + " (" + formatBytes(f.size) + ")</strong>";
        }).join(", ");
        showFileError(anchor,
          oversized.length === 1
            ? names + " exceeds the " + MAX_GALLERY_MB + " MB limit."
            : "These files exceed the limit and were skipped: " + names);
      }
 
      valid.forEach(function (f) {
        selectedFiles.push(f);
        var reader = new FileReader();
        reader.onload = function (ev) {
          var card = document.createElement("div");
          card.className = "gallery-card";
          var img = document.createElement("img");
          img.src = ev.target.result;
          img.className = "gallery-img";
          var badge = document.createElement("div");
          badge.style.cssText =
            "position:absolute;bottom:6px;left:6px;background:rgba(0,0,0,0.55);" +
            "color:#fff;font-size:10px;padding:2px 6px;border-radius:4px;pointer-events:none;";
          badge.textContent = formatBytes(f.size);
          var rm = document.createElement("button");
          rm.className = "gallery-remove-btn";
          rm.type = "button";
          rm.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
          (function (file) {
            rm.onclick = function () {
              var i = selectedFiles.indexOf(file);
              if (i > -1) selectedFiles.splice(i, 1);
              card.remove();
              syncFileInput();
            };
          })(f);
          card.appendChild(img);
          card.appendChild(badge);
          card.appendChild(rm);
          previewContainer.appendChild(card);
        };
        reader.readAsDataURL(f);
      });
 
      syncFileInput();
    });
  }
 
  function syncFileInput() {
    var dt = new DataTransfer();
    selectedFiles.forEach(function (f) { dt.items.add(f); });
    if (fileInput) fileInput.files = dt.files;
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     WORK ARRANGEMENT TAGS
  ═══════════════════════════════════════════════════════════ */
  var arrangementContainer = document.getElementById("arrangementTags");
  var arrangementInput     = document.getElementById("arrangementInput");
 
  if (arrangementContainer && arrangementInput) {
    function syncArrangement() {
      arrangementInput.value = Array.from(
        arrangementContainer.querySelectorAll(".tag.sel")
      ).map(function (t) { return t.dataset.val; }).join(", ");
    }
    arrangementContainer.querySelectorAll(".tag").forEach(function (tag) {
      tag.addEventListener("click", function () {
        tag.classList.toggle("sel");
        syncArrangement();
        if (typeof markDirty === "function") markDirty();
      });
    });
    syncArrangement();
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     DRAG & DROP — gallery zone
  ═══════════════════════════════════════════════════════════ */
  var uploadZone = document.querySelector(".upload-zone");
  if (uploadZone && fileInput) {
    uploadZone.addEventListener("dragover", function (e) {
      e.preventDefault(); uploadZone.classList.add("drag-over");
    });
    uploadZone.addEventListener("dragleave", function () {
      uploadZone.classList.remove("drag-over");
    });
    uploadZone.addEventListener("drop", function (e) {
      e.preventDefault();
      uploadZone.classList.remove("drag-over");
      Array.from(e.dataTransfer.files).forEach(function (f) { selectedFiles.push(f); });
      syncFileInput();
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }
 
 
  /* ═══════════════════════════════════════════════════════════
     DRAG & DROP — cover photo container
  ═══════════════════════════════════════════════════════════ */
  var coverContainer = document.getElementById("coverPhotoContainer");
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
      if (!e.dataTransfer.files.length) return;
      var f = e.dataTransfer.files[0];
      if (f.size > MAX_COVER_BYTES) {
        showFileError(coverHint || coverPreview,
          "Cover photo is too large (" + formatBytes(f.size) + "). Max " + MAX_COVER_MB + " MB.");
        return;
      }
      var dt = new DataTransfer();
      dt.items.add(f);
      coverInput.files = dt.files;
      coverInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }
 
}); // end DOMContentLoaded