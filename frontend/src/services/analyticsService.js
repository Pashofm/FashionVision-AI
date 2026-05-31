import { authenticatedFetch } from './api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

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
  getSummary({ period = 'weekly', startDate, endDate } = {}) {
    return apiGet('/api/analytics/dashboard/summary', {
      period,
      start_date: startDate,
      end_date: endDate,
    });
  },

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

  getSalesByHour(date = null) {
    return apiGet('/api/analytics/sales-by-hour', { date });
  },

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

  getComparison(period = 'weekly') {
    return apiGet('/api/analytics/comparison', { period });
  },

  getSalesTrend(days = 28) {
    return apiGet('/api/analytics/sales-trend', { days });
  },

  getInventoryAlerts() {
    return apiGet('/api/analytics/inventory-alerts');
  },

  getSalesGeneral() {
    return apiGet('/api/analytics/sales');
  },
};
