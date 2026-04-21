import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/login';
import Dashboard from './pages/Dashboard';
import Home from './pages/home';
import ClientDetection from './pages/ClientDetection';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Login />}
        />
        <Route
          path="/dashboard"
          element={<Dashboard />}
        />
        <Route
          path="/pago"
          element={<Home />}
        />
        <Route
          path="/detection"
          element={<ClientDetection />}
        />
        <Route
          path="/cliente"
          element={<ClientDetection />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
