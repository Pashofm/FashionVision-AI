import React from 'react';
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

// TODO: Reemplazar con datos reales del backend
const ventasSemanales = [
  { dia: 'Lun', Playera: 4, Pantalón: 2, Vestido: 1, Camisa: 3 },
  { dia: 'Mar', Playera: 3, Pantalón: 4, Vestido: 2, Camisa: 1 },
  { dia: 'Mié', Playera: 5, Pantalón: 1, Vestido: 3, Camisa: 2 },
  { dia: 'Jue', Playera: 2, Pantalón: 3, Vestido: 4, Camisa: 5 },
  { dia: 'Vie', Playera: 6, Pantalón: 5, Vestido: 2, Camisa: 3 },
  { dia: 'Sáb', Playera: 8, Pantalón: 6, Vestido: 5, Camisa: 4 },
  { dia: 'Dom', Playera: 3, Pantalón: 2, Vestido: 1, Camisa: 2 },
];

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page">
      <header>
        <div className="logo">FashionVision IA</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/pago')}>Pago</button>
          <button disabled>Inventario</button>
        </nav>
      </header>

      <main className="dashboard-container">

        {/* GRÁFICO DE VENTAS */}
        <section className="ventas-section">
          <h2 className="section-title">Ventas semanales</h2>
          <p className="section-subtitle">Cantidad de prendas vendidas por día</p>
          {/* TODO: Conectar con endpoint del backend cuando esté listo */}
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ventasSemanales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="dia" tick={{ fill: '#64748b' }} />
                <YAxis tick={{ fill: '#64748b' }} />
                <Tooltip />
                <Bar dataKey="Playera" fill="#4da6ff" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Pantalón" fill="#764ba2" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Vestido" fill="#f5576c" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Camisa" fill="#11998e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* APARTADOS INFERIORES */}
        <section className="actions-section">
          <div className="action-card pago-card">
            <h3>Realizar pago</h3>
            <button className="action-btn btn-pago" onClick={() => navigate('/pago')}>
              PAGO
            </button>
          </div>

          <div className="action-card inventario-card">
            <h3>Gestionar inventario</h3>
            <button className="action-btn btn-inventario" disabled>
              INVENTARIO
            </button>
          </div>
        </section>

      </main>
    </div>
  );
};

export default Dashboard;