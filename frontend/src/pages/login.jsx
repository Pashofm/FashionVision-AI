import React, { useState } from 'react';
import '../styles/login.css';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onLogin) {
      onLogin(email, password);
    } else {
      alert(`Login simulado\nEmail: ${email}\nContraseña: ${password}`);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>FashionVision IA</h1>
          <p>Sistema de reconocimiento de prendas</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Correo electrónico</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ingresa tu correo"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="ingresa tu contraseña"
              required
            />
          </div>

          <button type="submit" className="login-btn">
            Iniciar sesión
          </button>
        </form>

        <div className="login-footer">
          <p>¿Olvidaste tu contraseña?</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
