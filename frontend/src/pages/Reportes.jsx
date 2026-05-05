import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { performLogout } from '../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import '../styles/Reportes.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Reportes = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('week');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [salesData, setSalesData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [salesByCategory, setSalesByCategory] = useState([]);
  const userData = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    if (userData.role !== 'admin') {
      navigate('/');
      return;
    }
    fetchReportData();
  }, [navigate, userData.role, dateRange, startDate, endDate]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const headers = { 'Authorization': `Bearer ${token}` };

      let url = `${API_URL}/api/analytics/dashboard/summary`;
      const response = await fetch(url, { headers });
      if (!response.ok) {
        throw new Error('Error al cargar datos de reportes');
      }

      const data = await response.json();
      setSummary(data);
      setSalesByCategory(data.sales_by_category || []);

      const salesByHour = data.sales_by_hour || [];
      const hourlyData = Array.from({ length: 24 }, (_, i) => {
        const found = salesByHour.find(h => h.hour === i);
        return {
          hora: `${i.toString().padStart(2, '0')}:00`,
          ventas: found ? found.total_orders : 0,
          revenue: found ? found.total_revenue : 0
        };
      });
      setSalesData(hourlyData);

      setTopProducts(data.top_products || []);
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(value || 0);
  };

  const handleLogout = () => {
    performLogout();
    navigate('/');
  };

  const exportToCSV = () => {
    const headers = ['Producto', 'Categoría', 'Cantidad Vendida', 'Revenue', 'Órdenes'];
    const rows = topProducts.map(p => [
      p.product_name,
      p.category_name,
      p.total_quantity_sold,
      p.total_revenue,
      p.order_count
    ]);

    const csvContent = [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `reporte_ventas_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleDateRangeChange = (range) => {
    setDateRange(range);
    if (range !== 'custom') {
      setStartDate('');
      setEndDate('');
    }
  };

  if (!userData.role) return null;

  if (loading) {
    return (
      <div className="reportes-page">
        <header>
          <div className="logo">📊 Reportes - FashionVision</div>
          <nav>
            <button onClick={() => navigate('/dashboard')}>Dashboard</button>
            <button onClick={() => navigate('/inventory')}>Inventario</button>
            <button className="nav-active">Reportes</button>
          </nav>
          <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
        </header>
        <div className="reportes-container" style={{ textAlign: 'center', padding: '60px' }}>
          <p>Cargando datos de reportes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="reportes-page">
        <header>
          <div className="logo">📊 Reportes - FashionVision</div>
          <nav>
            <button onClick={() => navigate('/dashboard')}>Dashboard</button>
            <button onClick={() => navigate('/inventory')}>Inventario</button>
            <button className="nav-active">Reportes</button>
          </nav>
          <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
        </header>
        <div className="reportes-container" style={{ textAlign: 'center', padding: '60px' }}>
          <p style={{ color: '#f5576c' }}>{error}</p>
          <button onClick={fetchReportData} className="action-btn btn-inventario">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const COLORS = ['#4da6ff', '#764ba2', '#f5576c', '#11998e', '#fc8181', '#68d391'];

  const categoryData = salesByCategory.map((cat, index) => ({
    name: cat.category_name,
    cantidad: cat.total_quantity_sold,
    revenue: cat.total_revenue,
    color: COLORS[index % COLORS.length]
  }));

  return (
    <div className="reportes-page">
      <header>
        <div className="logo">📊 Reportes - FashionVision</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/inventory')}>Inventario</button>
          <button className="nav-active">Reportes</button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
      </header>

      <main className="reportes-container">
        <section className="reportes-header-section">
          <h1>Reportes y Estadísticas</h1>
          <p className="section-subtitle">Análisis detallado de ventas e inventario</p>

          <div className="date-range-selector">
            <label>Período:</label>
            <div className="range-buttons">
              <button
                className={dateRange === 'today' ? 'active' : ''}
                onClick={() => handleDateRangeChange('today')}
              >
                Hoy
              </button>
              <button
                className={dateRange === 'week' ? 'active' : ''}
                onClick={() => handleDateRangeChange('week')}
              >
                Esta Semana
              </button>
              <button
                className={dateRange === 'month' ? 'active' : ''}
                onClick={() => handleDateRangeChange('month')}
              >
                Este Mes
              </button>
              <button
                className={dateRange === 'custom' ? 'active' : ''}
                onClick={() => handleDateRangeChange('custom')}
              >
                Personalizado
              </button>
            </div>
            {dateRange === 'custom' && (
              <div className="custom-dates">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="Fecha inicio"
                />
                <span>hasta</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="Fecha fin"
                />
              </div>
            )}
          </div>
        </section>

        <section className="stats-cards">
          <div className="stat-card">
            <h3>Ventas del Período</h3>
            <p className="stat-value">{formatCurrency(summary?.today?.total_revenue || 0)}</p>
            <p className="stat-detail">{summary?.today?.total_orders || 0} órdenes</p>
          </div>
          <div className="stat-card">
            <h3>Ventas Mensuales</h3>
            <p className="stat-value">{formatCurrency(summary?.monthly_sales || 0)}</p>
            <p className="stat-detail">Últimos 30 días</p>
          </div>
          <div className="stat-card">
            <h3>Productos Vendidos</h3>
            <p className="stat-value">{summary?.today?.total_items_sold || 0}</p>
            <p className="stat-detail">Artículos</p>
          </div>
          <div className="stat-card">
            <h3>Tendencia Semanal</h3>
            <p className="stat-value">
              {summary?.comparison?.trend === 'up' ? '↑' : summary?.comparison?.trend === 'down' ? '↓' : '→'}
              {' '}{Math.abs(summary?.comparison?.percentage_change || 0)}%
            </p>
            <p className="stat-detail">vs semana anterior</p>
          </div>
        </section>

        <section className="charts-row">
          <div className="chart-card">
            <h2 className="section-title">Ventas por Hora</h2>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={salesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hora" tick={{ fill: '#64748b', fontSize: 10 }} />
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
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={categoryData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" tick={{ fill: '#64748b' }} />
                    <YAxis dataKey="name" type="category" tick={{ fill: '#64748b', fontSize: 11 }} width={100} />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Bar dataKey="revenue" name="Revenue" radius={[0, 4, 4, 0]}>
                      {categoryData.map((entry, index) => (
                        <div key={`bar-${index}`} style={{ backgroundColor: entry.color }} />
                      ))}
                    </Bar>
                  </BarChart>
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
          <div className="section-header">
            <div>
              <h2 className="section-title">Productos Más Vendidos</h2>
              <p className="section-subtitle">Rendimiento por producto</p>
            </div>
            <button className="action-btn btn-export" onClick={exportToCSV}>
              📥 Exportar CSV
            </button>
          </div>
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
                {topProducts.length > 0 ? (
                  topProducts.map((product) => (
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
      </main>
    </div>
  );
};

export default Reportes;
