/**
 * Servicio de Analytics para FashionVision AI.
 *
 * @module services/analyticsService
 * @description Cliente para los endpoints de análisis y reportes:
 *   - Dashboard (resumen diario, métricas)
 *   - Top productos más vendidos
 *   - Ventas por hora y por categoría
 *   - Comparativa entre períodos
 *   - Tendencia de ventas
 *   - Alertas de inventario
 */

import { authenticatedFetch } from './api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

/**
 * Realiza una petición GET autenticada con parámetros de query.
 * @param {string} path - Ruta del endpoint
 * @param {Object} [params={}] - Parámetros de query (se omiten null/undefined)
 * @returns {Promise<Object>} Datos de la respuesta
 */
async function apiGet(path, params = {}) {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') {
      url.searchParams.set(k, v);
    }
  });
  const response = await authenticatedFetch(url.toString());
  if (!response.ok) {
    throw new Error(`Error al obtener ${path}: ${response.statusText}`);
  }
  return response.json();
}

export const analyticsService = {
  /**
   * Obtiene el resumen del dashboard.
   * @param {Object} [opts] - Opciones de período
   * @param {string} [opts.period='weekly'] - Período: 'weekly' | 'monthly'
   * @param {string} [opts.startDate] - Fecha inicio (YYYY-MM-DD)
   * @param {string} [opts.endDate] - Fecha fin (YYYY-MM-DD)
   * @returns {Promise<Object>} DashboardSummary (today, sales_by_hour, etc.)
   */
  getSummary({ period = 'weekly', startDate, endDate } = {}) {
    return apiGet('/api/analytics/dashboard/summary', {
      period,
      start_date: startDate,
      end_date: endDate,
    });
  },

  /**
   * Obtiene los productos más vendidos.
   * @param {Object} [opts] - Opciones de filtro
   * @param {number} [opts.days=30] - Días hacia atrás
   * @param {string} [opts.startDate] - Fecha inicio
   * @param {string} [opts.endDate] - Fecha fin
   * @returns {Promise<Array>} Lista de DashboardTopProduct
   */
  getTopProducts({ days = 30, startDate, endDate } = {}) {
    const params = {};
    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    } else {
      params.days = days;
    }
    return apiGet('/api/analytics/top-products', params);
  },

  /**
   * Obtiene ventas agregadas por hora.
   * @param {string} [date=null] - Fecha específica (YYYY-MM-DD)
   * @returns {Promise<Array>} Lista de SalesByHour
   */
  getSalesByHour(date = null) {
    return apiGet('/api/analytics/sales-by-hour', { date });
  },

  /**
   * Obtiene ventas agregadas por categoría.
   * @param {Object} [opts] - Opciones de filtro
   * @returns {Promise<Array>} Lista de SalesByCategory
   */
  getSalesByCategory({ period = 'weekly', startDate, endDate } = {}) {
    const params = {};
    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    } else {
      params.period = period;
    }
    return apiGet('/api/analytics/sales-by-category', params);
  },

  /**
   * Compara ventas entre período actual y anterior.
   * @param {string} [period='weekly'] - Período
   * @returns {Promise<Object>} PeriodComparison
   */
  getComparison(period = 'weekly') {
    return apiGet('/api/analytics/comparison', { period });
  },

  /**
   * Obtiene tendencia de ventas diarias.
   * @param {number} [days=28] - Días hacia atrás
   * @returns {Promise<Array>} Datos de tendencia
   */
  getSalesTrend(days = 28) {
    return apiGet('/api/analytics/sales-trend', { days });
  },

  /**
   * Obtiene alertas de inventario (stock bajo / agotado).
   * @returns {Promise<Array>} Lista de InventoryAlert
   */
  getInventoryAlerts() {
    return apiGet('/api/analytics/inventory-alerts');
  },

  /**
   * Obtiene datos generales de ventas.
   * @returns {Promise<Object>} Ventas mensuales, semanales, diarias y por método de pago
   */
  getSalesGeneral() {
    return apiGet('/api/analytics/sales');
  },
};
