import React, { useState } from 'react';

const LoginForm = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');

  // Проверяем, есть ли токен в localStorage
  var token = localStorage.getItem('access_token');
  if (token) {
    alert('Токен найден. Перенаправляем на таблицу');
    window.location.href = '/'; // Перенаправляем на страницу аутентификации
  }
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://host.docker.internal:8080/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'grant_type=&username=' + encodeURIComponent(login) + '&password=' + encodeURIComponent(password) + '&scope=&client_id=&client_secret=',
      });

      if (!response.ok) {
        throw new Error('Failed to log in');
      }

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/'; // Redirect to '/'
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="container">
      <form id="login-form" onSubmit={handleSubmit}>
      <h2>Login</h2>
        <div className="input-group">
          <input
            type="text"
            id="login"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            placeholder="Username"
          />
        </div>
        <div className="input-group">
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
          />
        </div>
        <button type="submit" id="login-btn">Login</button>
      </form>
    </div>
  );
};

export default LoginForm;
