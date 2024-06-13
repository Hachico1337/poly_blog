document.querySelectorAll('[id^="newCommentForm"]').forEach(form => {
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Предотвращаем стандартную отправку формы
        const postId = this.id.split('-')[1]; // Извлекаем ID поста из ID формы
        const newCommentInput = document.getElementById(`newCommentInput-${postId}`);
        const commentsList = document.getElementById(`commentsList-${postId}`);
        const commentCounter = document.getElementById(`comment-counter-${postId}`);

        // Создаем новый элемент списка комментариев и устанавливаем его содержимое
        const newComment = document.createElement('li');
        newComment.textContent = newCommentInput.value;

        // Добавляем новый комментарий в список комментариев
        commentsList.appendChild(newComment);

        // Очищаем поле ввода после отправки
        newCommentInput.value = '';

        // Отправляем POST-запрос на сервер с содержимым комментария
        fetch(`/comment/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: newCommentInput.value
            }),
        })
       .then(response => response.json())
       .then(data => {
            if (data.status === 'success') {
                alert('Комментарий успешно добавлен!');
                updateCommentCounter(postId);
                // После успешной отправки комментария можно добавить его в список без перезагрузки страницы
                const username = data.username; // Предполагается, что сервер возвращает имя пользователя в ответе
                const timestamp = data.timestamp; // И предполагаемый формат времени
                const newItem = document.createElement('li');
                newItem.textContent = `${username}: ${newCommentInput.value} (${timestamp})`; // Форматируем строку комментария
                commentsList.insertBefore(newItem, commentsList.firstChild); // Добавляем новый комментарий в начало списка
            }
        })
       .catch(error => console.error('Ошибка отправки комментария:', error));
    });
});

function updateCommentCounter(postId) {
    const commentCounter = document.getElementById(`comment-counter-${postId}`);
    let currentCount = parseInt(commentCounter.innerText, 10);
    currentCount++;
    commentCounter.innerText = currentCount.toString();
}

function toggleCommentsWindow(postIndex) {
    const commentsWindow = document.getElementById(`commentsWindow-${postIndex}`);
    commentsWindow.style.display = commentsWindow.style.display === 'none'? 'block' : 'none';
    if (commentsWindow.style.display === 'block') {
        fetch(`/get-comments/${postIndex}`)
       .then(response => response.json())
       .then(data => {
            const commentsList = document.getElementById(`commentsList-${postIndex}`);
            commentsList.innerHTML = ''; // Очищаем список перед добавлением новых комментариев
            data.forEach(comment => {
                const newItem = document.createElement('li');
                newItem.textContent = `${comment.username}: ${comment.content} (${comment.timestamp})`;
                commentsList.appendChild(newItem);
            });
        })
       .catch(error => console.error('Ошибка загрузки комментариев:', error));
    }
}


function updateCommentCounter(postId) {
    const commentCounter = document.getElementById(`comment-counter-${postId}`);
    let currentCount = parseInt(commentCounter.innerText, 10);
    currentCount++;
    commentCounter.innerText = currentCount.toString();
}

function toggleCommentsWindow(postIndex) {
    const commentsWindow = document.getElementById(`commentsWindow-${postIndex}`);
    commentsWindow.style.display = commentsWindow.style.display === 'none'? 'block' : 'none';
    if (commentsWindow.style.display === 'block') {
        fetch(`/get-comments/${postIndex}`)
          .then(response => response.json())
          .then(data => {
                const commentsList = document.getElementById(`commentsList-${postIndex}`);
                commentsList.innerHTML = '';
                data.forEach(comment => {
                    const newItem = document.createElement('li');
                    newItem.textContent = `${comment.username}: ${comment.content} (${comment.timestamp})`;
                    commentsList.appendChild(newItem);
                });
            })
          .catch(error => console.error('Ошибка загрузки комментариев:', error));
    }
}

function incrementLikeCount(postId) {
    const likeCounter = document.getElementById(`like-counter-${postId}`);

    fetch(`/like/${postId}`, {
        method: 'POST',
    })
   .then(response => response.json())
   .then(data => {
        if (data.status === 'liked') {
            likeCounter.innerText = parseInt(likeCounter.innerText) + 1;
        } else {
            likeCounter.innerText = parseInt(likeCounter.innerText) - 1;
        }})
   .catch(error => console.error('Ошибка отправки лайка:', error));
}