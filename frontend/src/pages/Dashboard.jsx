import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem('user') || '{}');
    setUser(userData);
    if (userData.role !== 'admin') {
      navigate('/');
    }
  }, [navigate]);

  if (!user) return null;

  const ventasSemanales = [
    { dia: 'Lun', Playera: 4, Pantalon: 2, Vestido: 1, Camisa: 3 },
    { dia: 'Mar', Playera: 3, Pantalon: 4, Vestido: 2, Camisa: 1 },
    { dia: 'Mié', Playera: 5, Pantalon: 1, Vestido: 3, Camisa: 2 },
    { dia: 'Jue', Playera: 2, Pantalon: 3, Vestido: 4, Camisa: 5 },
    { dia: 'Vie', Playera: 6, Pantalon: 5, Vestido: 2, Camisa: 3 },
    { dia: 'Sáb', Playera: 8, Pantalon: 6, Vestido: 5, Camisa: 4 },
    { dia: 'Dom', Playera: 3, Pantalon: 2, Vestido: 1, Camisa: 2 },
  ];

  return (
    <div className="dashboard-page">
      <header>
        <div className="logo">⚙️ Admin - FashionVision</div>
        <nav>
          <button className="nav-active">Dashboard</button>
          <button onClick={() => navigate('/inventory')}>Inventario</button>
        </nav>
      </header>

      <main className="dashboard-container">
        <section className="ventas-section">
          <h2 className="section-title">Ventas semanales</h2>
          <p className="section-subtitle">Cantidad de prendas vendidas por día</p>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ventasSemanales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="dia" tick={{ fill: '#64748b' }} />
                <YAxis tick={{ fill: '#64748b' }} />
                <Tooltip />
                <Bar dataKey="Playera" fill="#4da6ff" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Pantalon" fill="#764ba2" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Vestido" fill="#f5576c" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Camisa" fill="#11998e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="actions-section">
          <div className="action-card inventario-card">
            <h3>Gestionar Inventario</h3>
            <p>Agregar, editar o eliminar productos y variants</p>
            <button className="action-btn btn-inventario" onClick={() => navigate('/inventory')}>
              INVENTARIO
            </button>
          </div>

          <div className="action-card analytics-card">
            <h3>Estadísticas</h3>
            <p>Ver análisis detallados de ventas</p>
            <button className="action-btn btn-analytics" disabled>
              PRÓXIMAMENTE
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
