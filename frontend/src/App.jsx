import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Cashier from './pages/Cashier';
import ClientDetection from './pages/ClientDetection';
import { SessionProvider } from './contexts/SessionContext';

function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/caja" element={<Cashier />} />
          <Route path="/cliente" element={<ClientDetection />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </SessionProvider>
    </BrowserRouter>
  );
}

export default App;
