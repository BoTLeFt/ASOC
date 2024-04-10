document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
  
    if (username === '' || password === '') {
      document.getElementById('username').classList.add('invalid');
      document.getElementById('password').classList.add('invalid');
      setTimeout(function() {
        document.getElementById('username').classList.remove('invalid');
        document.getElementById('password').classList.remove('invalid');
      }, 1000);
      return;
    }
  
    // Отправляем POST-запрос на сервер для получения токена
    let response = fetch('http://localhost:8080/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'grant_type=&username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password) + '&scope=&client_id=&client_secret='
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при получении токена');
        }
        return response.json();
    })
    .then(data => {
        console.log('Токен успешно получен:', data.access_token);
        // Сохраняем токен в локальном хранилище
        localStorage.setItem('access_token', data.access_token);
        // Перенаправляем пользователя на другую страницу
        window.location.href = '/user.html'; // Замените на вашу страницу
    })
    .catch(error => {
        console.error('Ошибка:', error);
        // Ваш код для обработки ошибки
    });
  });
  