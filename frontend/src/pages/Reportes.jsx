import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { performLogout } from '../services/api';
import { analyticsService } from '../services/analyticsService';
import { jsPDF } from 'jspdf';
import * as XLSX from 'xlsx';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import '../styles/Reportes.css';

const Reportes = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('week');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [salesData, setSalesData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [salesByCategory, setSalesByCategory] = useState([]);
  const userData = JSON.parse(localStorage.getItem('user') || '{}');

  const fetchReportData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (dateRange === 'today') {
        const today = new Date().toISOString().split('T')[0];
        const [salesByHourData, categoryData, topProductsData] = await Promise.all([
          analyticsService.getSalesByHour(today),
          analyticsService.getSalesByCategory({ period: 'daily' }),
          analyticsService.getTopProducts({ days: 1 }),
        ]);

        const hourlyData = Array.from({ length: 24 }, (_, i) => {
          const found = salesByHourData.find(h => h.hour === i);
          return {
            hora: `${i.toString().padStart(2, '0')}:00`,
            ventas: found ? found.total_orders : 0,
            revenue: found ? found.total_revenue : 0,
          };
        });
        setSalesData(hourlyData);
        setSalesByCategory(categoryData);
        setTopProducts(topProductsData);
        setSummary({
          today: {
            total_revenue: topProductsData.reduce((acc, p) => acc + p.total_revenue, 0),
            total_orders: topProductsData.reduce((acc, p) => acc + p.order_count, 0),
            total_items_sold: topProductsData.reduce((acc, p) => acc + p.total_quantity_sold, 0),
          },
          monthly_sales: topProductsData.reduce((acc, p) => acc + p.total_revenue, 0),
        });
        setComparison(null);
      } else if (dateRange === 'week') {
        const [summaryData, comparisonData] = await Promise.all([
          analyticsService.getSummary({ period: 'weekly' }),
          analyticsService.getComparison('weekly'),
        ]);

        setSummary(summaryData);
        setComparison(comparisonData);
        setSalesByCategory(summaryData.sales_by_category || []);
        setTopProducts(summaryData.top_products || []);

        const hourlyData = Array.from({ length: 24 }, (_, i) => {
          const found = (summaryData.sales_by_hour || []).find(h => h.hour === i);
          return {
            hora: `${i.toString().padStart(2, '0')}:00`,
            ventas: found ? found.total_orders : 0,
            revenue: found ? found.total_revenue : 0,
          };
        });
        setSalesData(hourlyData);
      } else if (dateRange === 'month') {
        const [summaryData, comparisonData] = await Promise.all([
          analyticsService.getSummary({ period: 'monthly' }),
          analyticsService.getComparison('monthly'),
        ]);

        setSummary(summaryData);
        setComparison(comparisonData);
        setSalesByCategory(summaryData.sales_by_category || []);
        setTopProducts(summaryData.top_products || []);

        const hourlyData = Array.from({ length: 24 }, (_, i) => {
          const found = (summaryData.sales_by_hour || []).find(h => h.hour === i);
          return {
            hora: `${i.toString().padStart(2, '0')}:00`,
            ventas: found ? found.total_orders : 0,
            revenue: found ? found.total_revenue : 0,
          };
        });
        setSalesData(hourlyData);
      } else if (dateRange === 'custom' && startDate && endDate) {
        const [summaryData, topProductsData, categoryData] = await Promise.all([
          analyticsService.getSummary({ startDate, endDate }),
          analyticsService.getTopProducts({ startDate, endDate }),
          analyticsService.getSalesByCategory({ startDate, endDate }),
        ]);

        setSummary(summaryData);
        setComparison(summaryData.comparison || null);
        setSalesByCategory(categoryData);
        setTopProducts(topProductsData);

        const hourlyData = Array.from({ length: 24 }, (_, i) => {
          const found = (summaryData.sales_by_hour || []).find(h => h.hour === i);
          return {
            hora: `${i.toString().padStart(2, '0')}:00`,
            ventas: found ? found.total_orders : 0,
            revenue: found ? found.total_revenue : 0,
          };
        });
        setSalesData(hourlyData);
      }
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [dateRange, startDate, endDate]);

  useEffect(() => {
    if (userData.role !== 'admin') {
      navigate('/');
      return;
    }
  }, [navigate, userData.role]);

  useEffect(() => {
    if (userData.role === 'admin' && dateRange !== 'custom') {
      fetchReportData();
    }
  }, [dateRange, fetchReportData, userData.role]);

  const handleApplyCustom = () => {
    if (dateRange === 'custom' && startDate && endDate) {
      fetchReportData();
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
      p.order_count,
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

  const exportPDF = () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let y = 22;

    doc.setFontSize(18);
    doc.text('Reporte de Ventas - FashionVision AI', 14, y);
    y += 10;

    doc.setFontSize(11);
    doc.text(`Generado: ${new Date().toLocaleString('es-MX')}`, 14, y);
    y += 7;
    doc.text(`Periodo: ${dateRange}`, 14, y);
    y += 12;

    const ticketProm = summary?.today?.total_orders > 0
      ? summary.today.total_revenue / summary.today.total_orders
      : 0;

    const metrics = [
      ['Ventas del Periodo', formatCurrency(summary?.today?.total_revenue || 0)],
      ['Ventas Mensuales', formatCurrency(summary?.monthly_sales || 0)],
      ['Productos Vendidos', String(summary?.today?.total_items_sold || 0)],
      ['Ticket Promedio', formatCurrency(ticketProm)],
    ];

    doc.setFontSize(13);
    doc.text('Metricas Principales', 14, y);
    y += 8;

    doc.setFontSize(10);
    metrics.forEach(([label, value]) => {
      doc.text(`${label}: ${value}`, 18, y);
      y += 7;
    });

    y += 5;
    doc.setFontSize(13);
    doc.text('Productos Mas Vendidos', 14, y);
    y += 8;

    const headers = ['Producto', 'Categoria', 'Cant.', 'Revenue', 'Ordenes'];
    const colWidths = [50, 35, 20, 35, 20];
    let x = 14;

    doc.setFontSize(9);
    headers.forEach((h, i) => {
      doc.text(h, x, y);
      x += colWidths[i];
    });
    y += 2;
    doc.line(14, y, pageWidth - 14, y);
    y += 6;

    doc.setFontSize(8);
    topProducts.forEach(p => {
      if (y > 275) {
        doc.addPage();
        y = 20;
      }
      x = 14;
      const row = [
        p.product_name.length > 22 ? p.product_name.substring(0, 20) + '..' : p.product_name,
        p.category_name.length > 14 ? p.category_name.substring(0, 12) + '..' : p.category_name,
        String(p.total_quantity_sold),
        formatCurrency(p.total_revenue),
        String(p.order_count),
      ];
      row.forEach((val, i) => {
        doc.text(val, x, y);
        x += colWidths[i];
      });
      y += 7;
    });

    const pageCount = doc.internal.pages.length;
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(
        `FashionVision AI - Pagina ${i} de ${pageCount}`,
        pageWidth / 2,
        290,
        { align: 'center' }
      );
    }

    doc.save(`reporte_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const exportExcel = () => {
    const wb = XLSX.utils.book_new();

    const ticketProm = summary?.today?.total_orders > 0
      ? summary.today.total_revenue / summary.today.total_orders
      : 0;

    const resumen = [
      ['Metrica', 'Valor'],
      ['Ventas del Periodo', formatCurrency(summary?.today?.total_revenue || 0)],
      ['Ventas Mensuales', formatCurrency(summary?.monthly_sales || 0)],
      ['Productos Vendidos', summary?.today?.total_items_sold || 0],
      ['Ticket Promedio', formatCurrency(ticketProm)],
      ['Total Transacciones', summary?.comparison?.current_period || 0],
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(resumen), 'Resumen');

    const topHeaders = ['Producto', 'Categoria', 'Cantidad Vendida', 'Revenue', 'Ordenes'];
    const topRows = topProducts.map(p => [
      p.product_name,
      p.category_name,
      p.total_quantity_sold,
      p.total_revenue,
      p.order_count,
    ]);
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([topHeaders, ...topRows]), 'Top Productos');

    const catHeaders = ['Categoria', 'Cantidad Vendida', 'Revenue', 'Ordenes'];
    const catRows = salesByCategory.map(c => [
      c.category_name,
      c.total_quantity_sold,
      c.total_revenue,
      c.order_count,
    ]);
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([catHeaders, ...catRows]), 'Ventas por Categoria');

    XLSX.writeFile(wb, `reporte_${new Date().toISOString().split('T')[0]}.xlsx`);
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
            <button onClick={() => navigate('/admin/catalog')}>Catálogo</button>
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
            <button onClick={() => navigate('/admin/catalog')}>Catálogo</button>
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
    color: COLORS[index % COLORS.length],
  }));

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return '\u2191';
      case 'down': return '\u2193';
      default: return '\u2192';
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up': return '#11998e';
      case 'down': return '#f5576c';
      default: return '#a0a0a0';
    }
  };

  return (
    <div className="reportes-page">
      <header>
        <div className="logo">📊 Reportes - FashionVision</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/inventory')}>Inventario</button>
          <button onClick={() => navigate('/admin/catalog')}>Catálogo</button>
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
              <>
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
                <button
                  className="action-btn btn-inventario"
                  onClick={handleApplyCustom}
                  disabled={!startDate || !endDate}
                >
                  Aplicar
                </button>
              </>
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
              {getTrendIcon(comparison?.trend)}
              {' '}{Math.abs(comparison?.percentage_change || 0)}%
            </p>
            <p className="stat-detail">vs período anterior</p>
          </div>
        </section>

        {comparison && (
          <section className="comparison-section">
            <h2 className="section-title">Comparativa de Períodos</h2>
            <div className="comparison-row">
              <div className="comparison-card">
                <span className="comp-label">Período Actual</span>
                <span className="comp-value">{formatCurrency(comparison.current_period)}</span>
              </div>
              <div className="comparison-card">
                <span className="comp-label">Período Anterior</span>
                <span className="comp-value">{formatCurrency(comparison.previous_period)}</span>
              </div>
              <div className="comparison-card">
                <span className="comp-label">Cambio</span>
                <span className="comp-value" style={{ color: getTrendColor(comparison.trend) }}>
                  {getTrendIcon(comparison.trend)} {comparison.percentage_change}%
                </span>
              </div>
              <div className="comparison-card">
                <span className="comp-label">Tendencia</span>
                <span className={`comp-badge ${comparison.trend}`}>
                  {comparison.trend === 'up' ? 'AL ALZA' : comparison.trend === 'down' ? 'A LA BAJA' : 'ESTABLE'}
                </span>
              </div>
            </div>
          </section>
        )}

        <section className="charts-row">
            <div className="chart-card">
              <h2 className="section-title">Ventas por Hora</h2>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={salesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="hora" tick={{ fill: '#a0a0a0', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#a0a0a0' }} allowDecimals={false} />
                    <Tooltip
                      formatter={(value) => [`${value} órdenes`, 'Órdenes']}
                      contentStyle={{
                        backgroundColor: '#1e1e2e',
                        border: '1px solid rgba(255,255,255,0.15)',
                        borderRadius: '8px',
                        color: '#e0e0e0',
                      }}
                    />
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
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis type="number" tick={{ fill: '#a0a0a0' }} />
                      <YAxis dataKey="name" type="category" tick={{ fill: '#a0a0a0', fontSize: 11 }} width={100} />
                      <Tooltip
                        formatter={(value) => [formatCurrency(value), 'Revenue']}
                        labelFormatter={(label) => label}
                        contentStyle={{
                          backgroundColor: '#1e1e2e',
                          border: '1px solid rgba(255,255,255,0.15)',
                          borderRadius: '8px',
                          color: '#e0e0e0',
                        }}
                      />
                    <Bar dataKey="revenue" name="Revenue" radius={[0, 4, 4, 0]}>
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
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
            <div className="export-buttons">
              <button className="action-btn btn-export" onClick={exportToCSV}>
                📥 CSV
              </button>
              <button className="action-btn btn-export" onClick={exportPDF}>
                📄 PDF
              </button>
              <button className="action-btn btn-export" onClick={exportExcel}>
                📊 Excel
              </button>
            </div>
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
