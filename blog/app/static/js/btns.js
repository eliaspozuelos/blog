function editPost(postId) {
    document.getElementById('edit-form-' + postId).style.display = 'block';
}

function cancelEdit(postId) {
    document.getElementById('edit-form-' + postId).style.display = 'none';
}

function submitEdit(postId) {
    const form = document.getElementById('edit-form-' + postId);
    const title = form.querySelector('.post-title-edit').value;
    const content = form.querySelector('.post-content-edit').value;

    fetch('/edit/' + postId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCookie('csrf_token')
        },
        body: JSON.stringify({title, content})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Publicación actualizada correctamente');
            location.reload(); // Recarga la página después de la actualización exitosa
        } else {
            alert('Error al actualizar la publicación');
        }
    })
    .catch(error => console.error('Error:', error));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
async function deletePost(postId) {
    const confirmDelete = confirm("¿Estás seguro de que quieres eliminar?");
    if (!confirmDelete) {
        // Si el usuario cancela, no se realiza ninguna acción
        return;
    }
    const response = await fetch(`/delete/${postId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    if (response.ok) {
        const result = await response.json();
        alert(result.message);
        
        // Suponiendo que tienes una función para actualizar la vista de las publicaciones
  
        location.reload(); // Recarga la página después de la actualización exitosa
    } else {
        alert("Hubo un error al intentar eliminar el post.");
    }
}
