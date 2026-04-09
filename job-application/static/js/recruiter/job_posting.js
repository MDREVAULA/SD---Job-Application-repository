  // Tab switching
  document.querySelectorAll('.form-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      document.querySelectorAll('.form-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + target).classList.add('active');
    });
  });

  // Work arrangement tags
  document.querySelectorAll('#arrangementTags .tag').forEach(tag => {
    tag.addEventListener('click', () => tag.classList.toggle('sel'));
    tag.addEventListener('click', updateArrangement);
  });
  function updateArrangement() {
    const selected = [...document.querySelectorAll('#arrangementTags .tag.sel')]
      .map(t => t.dataset.val).join(', ');
    document.getElementById('arrangementInput').value = selected;
  }
  updateArrangement();

  // Drag and drop on upload zone
  const uploadZone = document.querySelector('.upload-zone');
  const fileInput = document.getElementById('posterInput');
  if (uploadZone) {
    uploadZone.addEventListener('dragover', e => {
      e.preventDefault();
      uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', e => {
      e.preventDefault();
      uploadZone.classList.remove('drag-over');
      fileInput.files = e.dataTransfer.files;
      fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }