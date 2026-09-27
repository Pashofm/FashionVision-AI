import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  login,
  refreshToken,
  detectClothes,
  checkHealth,
  getProducts,
  getCategories,
  createCart,
  getCarts,
  addCartItem,
  updateCartStatus,
  submitCart,
  approveCart,
  rejectCart,
  processPayment,
  getLowStockProducts,
  adjustInventory,
  posInitializePayment,
  posWaitForCard,
  posProcessPayment,
  getStoredUser,
  isAuthenticated
} from '../../services/api';

vi.stubGlobal('localStorage', {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
});

describe('API Service', () => {
  const BASE_URL = import.meta.env.VITE_API_URL || '/';
  const API_URL = BASE_URL === '/' || BASE_URL === '/api' ? '' : BASE_URL;
  const mockToken = 'mock-access-token';

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.getItem.mockImplementation((key) => {
      if (key === 'access_token') return mockToken;
      if (key === 'user') return JSON.stringify({ id: '1', name: 'Test', role: 'admin' });
      return null;
    });
  });

  describe('Authentication', () => {
    it('login should be a function', () => {
      expect(typeof login).toBe('function');
    });

    it('refreshToken should be a function', () => {
      expect(typeof refreshToken).toBe('function');
    });

    it('getStoredUser should return parsed user object', () => {
      const user = getStoredUser();
      expect(user).toEqual({ id: '1', name: 'Test', role: 'admin' });
    });

    it('isAuthenticated should return boolean', () => {
      const result = isAuthenticated();
      expect(typeof result).toBe('boolean');
    });
  });

  describe('Health Check', () => {
    it('checkHealth should be a function', () => {
      expect(typeof checkHealth).toBe('function');
    });

    it('checkHealth should call correct endpoint', async () => {
      global.fetch = vi.fn(() => Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy', model_loaded: true })
      }));

      const result = await checkHealth();
      expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/health`);
    });
  });

  describe('Detection', () => {
    it('detectClothes should be a function', () => {
      expect(typeof detectClothes).toBe('function');
    });
  });

  describe('Products', () => {
    it('getProducts should be a function', () => {
      expect(typeof getProducts).toBe('function');
    });

    it('getCategories should be a function', () => {
      expect(typeof getCategories).toBe('function');
    });
  });

  describe('Cart Operations', () => {
    it('createCart should be a function', () => {
      expect(typeof createCart).toBe('function');
    });

    it('getCarts should be a function', () => {
      expect(typeof getCarts).toBe('function');
    });

    it('addCartItem should be a function', () => {
      expect(typeof addCartItem).toBe('function');
    });

    it('updateCartStatus should be a function', () => {
      expect(typeof updateCartStatus).toBe('function');
    });

    it('submitCart should be a function', () => {
      expect(typeof submitCart).toBe('function');
    });

    it('approveCart should be a function', () => {
      expect(typeof approveCart).toBe('function');
    });

    it('rejectCart should be a function', () => {
      expect(typeof rejectCart).toBe('function');
    });

    it('processPayment should be a function', () => {
      expect(typeof processPayment).toBe('function');
    });
  });

  describe('Inventory', () => {
    it('getLowStockProducts should be a function', () => {
      expect(typeof getLowStockProducts).toBe('function');
    });

    it('adjustInventory should be a function', () => {
      expect(typeof adjustInventory).toBe('function');
    });
  });

  describe('POS Terminal', () => {
    it('posInitializePayment should be a function', () => {
      expect(typeof posInitializePayment).toBe('function');
    });

    it('posWaitForCard should be a function', () => {
      expect(typeof posWaitForCard).toBe('function');
    });

    it('posProcessPayment should be a function', () => {
      expect(typeof posProcessPayment).toBe('function');
    });
  });
});

describe('API Integration Tests', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  describe('login', () => {
    it('should make POST request to /api/auth/login', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'token',
          refresh_token: 'refresh',
          expires_in: 3600,
          user: { id: '1', name: 'Test', role: 'admin' }
        })
      });

      await login('test@example.com', 'password');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'test@example.com', password: 'password' })
        })
      );
    });

    it('does not duplicate the API prefix when VITE_API_URL is /api', async () => {
      vi.stubEnv('VITE_API_URL', '/api');
      vi.resetModules();
      const { login: loginWithApiPrefix } = await import('../../services/api');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'token',
          refresh_token: 'refresh',
          expires_in: 3600,
          user: { id: '1', name: 'Test', role: 'admin' }
        })
      });

      await loginWithApiPrefix('test@example.com', 'password');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({ method: 'POST' })
      );

      vi.unstubAllEnvs();
    });
  });

  describe('checkHealth', () => {
    it('should return health status from API', async () => {
      const mockHealth = { status: 'healthy', model_loaded: true };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth
      });

      const result = await checkHealth();
      expect(result).toEqual(mockHealth);
    });
  });

  describe('getProducts', () => {
    it('should fetch products from the API', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      await getProducts();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/products')
      );
    });
  });
});
