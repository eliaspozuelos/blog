function likePost(postId) {
    fetch(`/like/${postId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ postId: postId }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const likeCount = document.getElementById(`like-count-${postId}`);
          likeCount.textContent = `${data.likes} Likes`;
        } else {
          alert('Error al dar like.');
        }
      })
      .catch(error => console.error('Error:', error));
  }
  
