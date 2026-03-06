import React, { useState } from 'react';
import Home from './pages/home';
import Login from './pages/login';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = (email, password) => {
    console.log('Login attempt:', email, password);
    setIsLoggedIn(true);
  };

  return (
    <div className="App">
      {isLoggedIn ? <Home /> : <Login onLogin={handleLogin} />}
    </div>
  );
}

export default App;
