import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Cashier from './pages/Cashier';
import ClientDetection from './pages/ClientDetection';
import Reportes from './pages/Reportes';
import CatalogManager from './pages/CatalogManager';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/caja" element={<Cashier />} />
        <Route path="/cliente" element={<ClientDetection />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="/admin/catalog" element={<CatalogManager />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
