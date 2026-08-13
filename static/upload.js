const sheetUploadForm = document.getElementById('sheetUploadForm');
const keyUploadForm = document.getElementById('keyUploadForm');
const submit3 = document.getElementById('submit3');
const imageInput = document.getElementById('imageInput');
const csvInput = document.getElementById('csvInput');
const sheetSelectedFiles = document.getElementById('sheetSelectedFiles');
const keySelectedFiles = document.getElementById('keySelectedFiles');

function setInputFiles(input, files) {
  const dataTransfer = new DataTransfer();
  files.forEach((file) => dataTransfer.items.add(file));
  input.files = dataTransfer.files;
}

function renderSelectedFiles(input, listEl, label) {
  listEl.innerHTML = '';

  if (!input.files || input.files.length === 0) {
    listEl.innerHTML = `<span class="empty-state">No ${label} selected</span>`;
    return;
  }

  Array.from(input.files).forEach((file, index) => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <span>${file.name}</span>
      <button type="button" class="remove-file" data-type="${label}" data-index="${index}">Remove</button>
    `;
    listEl.appendChild(item);
  });
}

function removeSelectedFile(input, listEl, type, indexToRemove) {
  const files = Array.from(input.files || []);
  files.splice(indexToRemove, 1);
  setInputFiles(input, files);
  renderSelectedFiles(input, listEl, type);
}

imageInput.addEventListener('change', function () {
  renderSelectedFiles(imageInput, sheetSelectedFiles, 'sheet');
});

csvInput.addEventListener('change', function () {
  renderSelectedFiles(csvInput, keySelectedFiles, 'key');
});

document.addEventListener('click', function (event) {
  const removeBtn = event.target.closest('.remove-file');
  if (!removeBtn) return;

  const type = removeBtn.dataset.type;
  const index = Number(removeBtn.dataset.index);

  if (type === 'sheet') {
    removeSelectedFile(imageInput, sheetSelectedFiles, 'sheet', index);
  } else if (type === 'key') {
    removeSelectedFile(csvInput, keySelectedFiles, 'key', index);
  }
});

sheetUploadForm.addEventListener('submit', function (event) {
  event.preventDefault();

  if (!imageInput.files.length) {
    Swal.fire({
      icon: 'warning',
      title: 'No sheet selected',
      text: 'Please choose one or more answer-sheet images.'
    });
    return;
  }

  const formData = new FormData();
  Array.from(imageInput.files).forEach((file) => {
    formData.append('file1', file, file.name);
  });

  fetch(sheetUploadForm.action, {
    method: 'POST',
    body: formData
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      Swal.fire({
        position: 'top-end',
        icon: 'success',
        title: data.message || 'Answer sheets uploaded successfully',
        showConfirmButton: false,
        timer: 1500
      });
    })
    .catch(function (error) {
      console.error(error);
      Swal.fire({
        icon: 'error',
        title: 'Sheet upload failed',
        text: 'Please try again.'
      });
    });
});

keyUploadForm.addEventListener('submit', function (event) {
  event.preventDefault();

  if (!csvInput.files.length) {
    Swal.fire({
      icon: 'warning',
      title: 'No CSV selected',
      text: 'Please choose the answer-key CSV file.'
    });
    return;
  }

  const formData = new FormData();
  formData.append('file2', csvInput.files[0], csvInput.files[0].name);

  fetch(keyUploadForm.action, {
    method: 'POST',
    body: formData
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      Swal.fire({
        position: 'top-end',
        icon: 'success',
        title: data.message || 'Answer key uploaded successfully',
        showConfirmButton: false,
        timer: 1500
      });
    })
    .catch(function (error) {
      console.error(error);
      Swal.fire({
        icon: 'error',
        title: 'Key upload failed',
        text: 'Please try again.'
      });
    });
});

submit3.addEventListener('click', function (event) {
  event.preventDefault();

  fetch('/load', {
    method: 'GET'
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      document.getElementById('resultText').innerText = data.messages.join('\n');
      document.getElementById('downloadLink').href = data.filepath;
      document.getElementById('downloadLink').style.display = 'inline-flex';

      Swal.fire({
        title: 'RESULT',
        html: data.messages.join('<br>'),
        icon: 'success'
      });
    })
    .catch(function (error) {
      console.error(error);
      Swal.fire({
        icon: 'error',
        title: 'Evaluation failed',
        text: 'Please upload the files first.'
      });
    });
});

renderSelectedFiles(imageInput, sheetSelectedFiles, 'sheet');
renderSelectedFiles(csvInput, keySelectedFiles, 'key');