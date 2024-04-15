const image1 = document.getElementById('image1');
const image2 = document.getElementById('image2');
const preview1 = document.getElementById('preview1');
const preview2 = document.getElementById('preview2');
const submit3 = document.getElementById('submit3');
document.getElementById('file1-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var formData = new FormData(event.target);
    fetch(event.target.action, {
      method: 'POST',
      body: formData
    }).then(function(response) {
      return response.json();
    }).then(function(data) {
      Swal.fire({
        position: "top-end",
        icon: "success",
        title: "Your Image has been saved",
        showConfirmButton: false,
        timer: 1500
      });
      // alert(data.message);
    }).catch(function(error) {
      console.error(error);
    });
  });
document.getElementById('file2-form').addEventListener('submit', function(event) {
  event.preventDefault();
  var formData = new FormData(event.target);
  fetch(event.target.action, {
    method: 'POST',
    body: formData
  }).then(function(response) {
    return response.json();
  }).then(function(data) {
    Swal.fire({
      position: "top-end",
      icon: "success",
      title: "Your File has been saved",
      showConfirmButton: false,
      timer: 1500
    });
    // alert(data.message);
  }).catch(function(error) {
    console.error(error);
  });
  });
image1.addEventListener('change', function() {
    previewImage(this, preview1);
});
image2.addEventListener('change', function() {
    previewImage(this, preview2);
});
function previewImage(input, preview) {
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        preview.style.backgroundImage = `url(${e.target.result})`;
    }
    reader.readAsDataURL(file);
}
submit3.addEventListener('click', function(event) {
    event.preventDefault();
    fetch('/load', {
        method: 'GET'  // Send a GET request to the /load route
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
      Swal.fire({
        title: "RESULT",
        html:data.messages.join('<br>'),
        // text: data.messages,
        icon: "success"
      });
        // alert(data.messages.join('\n')).join('\n');
        document.getElementById('downloadLink').href = data.filepath;
      // alert(data.message); 
    })
    .catch(function(error) {
        console.error(error);
    });
});