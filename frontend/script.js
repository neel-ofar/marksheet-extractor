// script.js ke sabse top pe yeh daal do
const BACKEND_URL = "https://marksheet-extractor-ciik.onrender.com/docs";  // ← YAHAN APNA REAL RENDER BACKEND URL DAAL DO




document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileInfo = document.getElementById('file-info');
  const previewImg = document.getElementById('preview-img');
  const pdfPreview = document.getElementById('pdf-preview');
  const extractBtn = document.getElementById('extract-btn');
  const loading = document.getElementById('loading');
  const resultDiv = document.getElementById('result');
  const errorDiv = document.getElementById('error');

  let selectedFile = null;

  // Click to open file picker
  dropZone.addEventListener('click', () => fileInput.click());

  // Drag & drop
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.style.borderColor = '#00d4ff';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#5c9ead';
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.style.borderColor = '#5c9ead';
    handleFiles(e.dataTransfer.files);
  });

  fileInput.addEventListener('change', e => handleFiles(e.target.files));

  function handleFiles(files) {
    if (files.length === 0) return;
    selectedFile = files[0];

    fileInfo.textContent = `${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(1)} MB)`;

    extractBtn.disabled = false;

    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
      if (selectedFile.type.startsWith('image/')) {
        previewImg.src = e.target.result;
        previewImg.style.display = 'block';
        pdfPreview.style.display = 'none';
      } else if (selectedFile.type === 'application/pdf') {
        pdfPreview.src = e.target.result;
        pdfPreview.style.display = 'block';
        previewImg.style.display = 'none';
      }
    };
    reader.readAsDataURL(selectedFile);
  }

  // Extract button click
  extractBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    loading.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    extractBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${BACKEND_URL}/extract`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();

      // Show result
      document.getElementById('name-value').textContent = data.name?.value || '—';
      document.getElementById('roll-value').textContent = data.roll_no?.value || '—';
      document.getElementById('result-value').textContent = data.result?.value || '—';

      const tbody = document.querySelector('#subjects-table tbody');
      tbody.innerHTML = '';
      if (data.subjects?.length) {
        data.subjects.forEach(sub => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${sub.subject || '—'}</td>
            <td>${sub.obtained || '—'}</td>
            <td>${sub.max || '—'}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      document.getElementById('json-output').textContent = JSON.stringify(data, null, 2);

      resultDiv.classList.remove('hidden');
    } catch (err) {
      errorDiv.textContent = err.message;
      errorDiv.classList.remove('hidden');
    } finally {
      loading.classList.add('hidden');
      extractBtn.disabled = false;
    }
  });
});
