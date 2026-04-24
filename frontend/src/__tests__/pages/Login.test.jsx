import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { login, checkHealth } from '../../services/api';

vi.mock('../../services/api', () => ({
  login: vi.fn(),
  checkHealth: vi.fn(),
  getStoredUser: vi.fn(() => null),
  isAuthenticated: vi.fn(() => false)
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

import Login from '../../pages/Login';

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('renders login form', () => {
      renderLogin();
      expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/contraseña/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument();
    });

    it('renders logo/brand element', () => {
      renderLogin();
      expect(screen.getByText(/fashionvision/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation errors for empty fields', async () => {
      renderLogin();
      const user = userEvent.setup();

      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(screen.getByText(/campos requeridos/i)).toBeInTheDocument();
      });
    });

    it('validates email format', async () => {
      renderLogin();
      const user = userEvent.setup();

      const emailInput = screen.getByPlaceholderText(/email/i);
      await user.type(emailInput, 'invalid-email');

      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(screen.getByText(/formato de email inválido/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication Flow', () => {
    it('calls login API with correct credentials', async () => {
      login.mockResolvedValueOnce({
        access_token: 'test-token',
        user: { id: '1', name: 'Test User', role: 'admin' }
      });

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'admin@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'password123');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith('admin@test.com', 'password123');
      });
    });

    it('navigates to dashboard on admin login success', async () => {
      login.mockResolvedValueOnce({
        access_token: 'test-token',
        user: { id: '1', name: 'Admin', role: 'admin' }
      });

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'admin@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('navigates to caja on cashier login success', async () => {
      login.mockResolvedValueOnce({
        access_token: 'test-token',
        user: { id: '2', name: 'Cashier', role: 'cashier' }
      });

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'cashier@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'cashier123');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/caja');
      });
    });

    it('navigates to cliente on client login success', async () => {
      login.mockResolvedValueOnce({
        access_token: 'test-token',
        user: { id: '3', name: 'Client', role: 'client' }
      });

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'client@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'client123');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/cliente');
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message on login failure', async () => {
      login.mockRejectedValueOnce(new Error('Credenciales inválidas'));

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'wrong@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'wrongpass');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      await waitFor(() => {
        expect(screen.getByText(/credenciales inválidas/i)).toBeInTheDocument();
      });
    });

    it('shows loading state during login', async () => {
      login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      renderLogin();
      const user = userEvent.setup();

      await user.type(screen.getByPlaceholderText(/email/i), 'test@test.com');
      await user.type(screen.getByPlaceholderText(/contraseña/i), 'password');
      await user.click(screen.getByRole('button', { name: /entrar/i }));

      expect(screen.getByText(/cargando/i)).toBeInTheDocument();
    });
  });
});
