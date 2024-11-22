document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');

    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function (event) {
            const file = event.target.files[0];

            if (file) {
                const reader = new FileReader();

                reader.onload = function (e) {
                    imagePreview.src = e.target.result; // Asignar la imagen cargada al src
                    imagePreview.style.display = 'block'; // Mostrar el elemento <img>
                };

                reader.readAsDataURL(file); // Leer el archivo como URL de datos
            } else {
                imagePreview.src = '#'; // Restablecer el src si no hay archivo
                imagePreview.style.display = 'none'; // Ocultar la previsualización
            }
        });
    }
});
