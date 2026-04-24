import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { performLogout } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import './Dashboard.css';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const COLORS = ['#4da6ff', '#764ba2', '#f5576c', '#11998e', '#fc8181', '#68d391'];

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [salesData, setSalesData] = useState([]);
  const userData = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    if (userData.role !== 'admin') {
      navigate('/');
      return;
    }
    fetchDashboardData();
  }, [navigate, userData.role]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const response = await fetch(`${API_URL}/api/analytics/dashboard/summary`, { headers });
      if (!response.ok) {
        throw new Error('Error al cargar datos del dashboard');
      }

      const data = await response.json();
      setSummary(data);

      const hourData = data.sales_by_hour || [];
      const formattedHourData = Array.from({ length: 24 }, (_, i) => {
        const found = hourData.find(h => h.hour === i);
        return {
          hour: `${i.toString().padStart(2, '0')}:00`,
          ventas: found ? found.total_orders : 0,
          revenue: found ? found.total_revenue : 0,
        };
      });
      setSalesData(formattedHourData);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(value);
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return '↑';
      case 'down': return '↓';
      default: return '→';
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up': return '#11998e';
      case 'down': return '#f5576c';
      default: return '#94a3b8';
    }
  };

  const handleLogout = () => {
    performLogout();
    navigate('/');
  };

  if (!userData.role) return null;

  if (loading) {
    return (
      <div className="dashboard-page">
        <header>
          <div className="logo">⚙️ Admin - FashionVision</div>
          <nav>
            <button className="nav-active">Dashboard</button>
            <button onClick={() => navigate('/inventory')}>Inventario</button>
          </nav>
          <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
        </header>
        <div className="dashboard-container" style={{ textAlign: 'center', padding: '60px' }}>
          <p>Cargando datos del dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <header>
          <div className="logo">⚙️ Admin - FashionVision</div>
          <nav>
            <button className="nav-active">Dashboard</button>
            <button onClick={() => navigate('/inventory')}>Inventario</button>
          </nav>
          <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
        </header>
        <div className="dashboard-container" style={{ textAlign: 'center', padding: '60px' }}>
          <p style={{ color: '#f5576c' }}>{error}</p>
          <button onClick={fetchDashboardData} className="action-btn btn-inventario">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const pieData = summary?.sales_by_category?.map((cat, index) => ({
    name: cat.category_name,
    value: cat.total_quantity_sold,
    color: COLORS[index % COLORS.length],
  })) || [];

  return (
    <div className="dashboard-page">
      <header>
        <div className="logo">⚙️ Admin - FashionVision</div>
        <nav>
          <button className="nav-active">Dashboard</button>
          <button onClick={() => navigate('/inventory')}>Inventario</button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
      </header>

      <main className="dashboard-container">
        <section className="stats-cards">
          <div className="stat-card">
            <h3>Ventas de Hoy</h3>
            <p className="stat-value">{formatCurrency(summary?.today?.total_revenue || 0)}</p>
            <p className="stat-detail">{summary?.today?.total_orders || 0} órdenes</p>
          </div>
          <div className="stat-card">
            <h3>Ventas Semanales</h3>
            <p className="stat-value">{formatCurrency(summary?.weekly_sales || 0)}</p>
            <p className="stat-detail">
              <span style={{ color: getTrendColor(summary?.comparison?.trend), fontWeight: 'bold' }}>
                {getTrendIcon(summary?.comparison?.trend)} {Math.abs(summary?.comparison?.percentage_change || 0)}%
              </span>
              {' '}vs semana anterior
            </p>
          </div>
          <div className="stat-card">
            <h3>Ventas Mensuales</h3>
            <p className="stat-value">{formatCurrency(summary?.monthly_sales || 0)}</p>
            <p className="stat-detail">Últimos 30 días</p>
          </div>
          <div className="stat-card">
            <h3>Productos Vendidos (Hoy)</h3>
            <p className="stat-value">{summary?.today?.total_items_sold || 0}</p>
            <p className="stat-detail">Artículos</p>
          </div>
        </section>

        <section className="charts-row">
          <div className="chart-card">
            <h2 className="section-title">Ventas por Hora (Hoy)</h2>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={salesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#64748b' }} />
                  <Tooltip />
                  <Bar dataKey="ventas" fill="#4da6ff" radius={[4, 4, 0, 0]} name="Órdenes" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <h2 className="section-title">Ventas por Categoría</h2>
            <div className="chart-wrapper">
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8' }}>
                  Sin datos de ventas
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="top-products-section">
          <h2 className="section-title">Productos Más Vendidos</h2>
          <p className="section-subtitle">Últimos 30 días</p>
          <div className="products-table-wrapper">
            <table className="products-table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Categoría</th>
                  <th>Cantidad Vendida</th>
                  <th>Revenue</th>
                  <th>Órdenes</th>
                </tr>
              </thead>
              <tbody>
                {summary?.top_products?.length > 0 ? (
                  summary.top_products.map((product) => (
                    <tr key={product.product_id}>
                      <td>{product.product_name}</td>
                      <td>{product.category_name}</td>
                      <td>{product.total_quantity_sold}</td>
                      <td>{formatCurrency(product.total_revenue)}</td>
                      <td>{product.order_count}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', color: '#94a3b8' }}>
                      Sin ventas registradas
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {summary?.inventory_alerts?.length > 0 && (
          <section className="alerts-section">
            <h2 className="section-title">Alertas de Inventario</h2>
            <p className="section-subtitle">Productos con stock bajo o agotado</p>
            <div className="alerts-list">
              {summary.inventory_alerts.map((alert) => (
                <div key={alert.variant_id} className={`alert-item ${alert.status}`}>
                  <div className="alert-info">
                    <strong>{alert.product_name}</strong>
                    <span>{alert.variant_description}</span>
                    <span className="alert-sku">SKU: {alert.sku_variant}</span>
                  </div>
                  <div className="alert-stock">
                    <span className={`stock-badge ${alert.status}`}>
                      {alert.status === 'out_of_stock' ? 'AGOTADO' : 'STOCK BAJO'}
                    </span>
                    <span className="stock-count">
                      {alert.quantity_available} disponibles
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="actions-section">
          <div className="action-card inventario-card">
            <h3>Gestionar Inventario</h3>
            <p>Agregar, editar o eliminar productos y variantes</p>
            <button className="action-btn btn-inventario" onClick={() => navigate('/inventory')}>
              INVENTARIO
            </button>
          </div>

          <div className="action-card analytics-card">
            <h3>Estadísticas Avanzadas</h3>
            <p>Ver análisis detallados y reportes</p>
            <button className="action-btn btn-analytics" onClick={() => alert('Próximamente: Reportes detallados')}>
              VER REPORTES
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;