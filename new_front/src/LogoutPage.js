import React from 'react';

const LogoutPage = () => {

  // Проверяем, есть ли токен в localStorage
  var token = localStorage.getItem('access_token');
  if (token) {
    alert('Токен найден. Очищен и перенаправлен на авторизацию');
    localStorage.clear();
    window.location.href = '/login'; // Перенаправляем на страницу аутентификации
  }
  window.location.href = '/login'; // Перенаправляем на страницу аутентификации

  return (
    <div className="container">
      <h2>Logout</h2>
    </div>
  );
};

export default LogoutPage;
