import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPendingCarts, approveCart, rejectCart, markCartPaid } from '../services/api';
import '../styles/home.css';

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('es-MX', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const Cashier = () => {
  const [carts, setCarts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role !== 'cashier') {
      navigate('/');
      return;
    }
    fetchPendingCarts();
  }, [navigate]);

  const fetchPendingCarts = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getPendingCarts();
      setCarts(data);
    } catch (err) {
      console.error('Error fetching carts:', err);
      setError('Error al cargar los pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (cartId) => {
    try {
      setProcessingId(cartId);
      await approveCart(cartId);
      await fetchPendingCarts();
    } catch (err) {
      setError('Error al aprobar pedido');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (cartId) => {
    try {
      setProcessingId(cartId);
      await rejectCart(cartId, 'Rechazado en caja');
      await fetchPendingCarts();
    } catch (err) {
      setError('Error al rechazar pedido');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  const handleMarkPaid = async (cartId) => {
    try {
      setProcessingId(cartId);
      await markCartPaid(cartId);
      await fetchPendingCarts();
    } catch (err) {
      setError('Error al procesar pago');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="home-page">
      <header>
        <div className="logo">💰 Caja - FashionVision</div>
        <nav>
          <button className="nav-active">Caja</button>
        </nav>
      </header>

      <main className="container">
        {error && <div className="error-message">{error}</div>}

        <div className="section-header">
          <h2>📋 Pedidos Pendientes</h2>
          <button className="btn-primary" onClick={fetchPendingCarts}>
            🔄 Actualizar
          </button>
        </div>

        {loading ? (
          <div className="preview-loading">
            <div className="spinner"></div>
            <p>Cargando pedidos...</p>
          </div>
        ) : carts.length === 0 ? (
          <div className="no-detection">
            <h3>No hay pedidos pendientes</h3>
            <p>Los pedidos de los clientes aparecerán aquí</p>
          </div>
        ) : (
          <div className="carts-grid">
            {carts.map((cart) => (
              <div key={cart.id} className="cart-card">
                <div className="cart-card-header">
                  <span className="cart-id">#{cart.id.slice(0, 8).toUpperCase()}</span>
                  <span className="cart-date">{formatDate(cart.created_at)}</span>
                </div>

                <div className="cart-items">
                  {cart.items.map((item) => (
                    <div key={item.id} className="cart-item-row">
                      <div className="cart-item-info">
                        <span className="cart-item-name">{item.product?.name || 'Producto'}</span>
                        <span className="cart-item-qty">Cantidad: {item.quantity}</span>
                      </div>
                      <span className="cart-item-price">${(item.unit_price * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                <div className="cart-total">
                  <span>Total</span>
                  <span className="cart-total-amount">${cart.total?.toFixed(2) || '0.00'}</span>
                </div>

                <div className="cart-actions">
                  {cart.status === 'submitted' && (
                    <>
                      <button
                        className="btn-secondary"
                        onClick={() => handleApprove(cart.id)}
                        disabled={processingId === cart.id}
                      >
                        ✓ Aprobar
                      </button>
                      <button
                        className="btn-outline"
                        onClick={() => handleReject(cart.id)}
                        disabled={processingId === cart.id}
                      >
                        ✕ Rechazar
                      </button>
                    </>
                  )}
                  {cart.status === 'processing' && (
                    <button
                      className="btn-primary"
                      onClick={() => handleMarkPaid(cart.id)}
                      disabled={processingId === cart.id}
                    >
                      💳 Cobrar y Finalizar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <style>{`
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .section-header h2 {
          margin: 0;
          font-size: 20px;
          color: #1e293b;
        }
        .carts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }
        .cart-card {
          background: white;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
          overflow: hidden;
          transition: all 0.2s;
        }
        .cart-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        .cart-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        .cart-id {
          font-weight: 700;
          font-size: 14px;
          font-family: monospace;
        }
        .cart-date {
          font-size: 12px;
          opacity: 0.9;
        }
        .cart-items {
          padding: 12px 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          max-height: 180px;
          overflow-y: auto;
        }
        .cart-item-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f1f5f9;
        }
        .cart-item-row:last-child {
          border-bottom: none;
        }
        .cart-item-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .cart-item-name {
          font-weight: 500;
          color: #1e293b;
          font-size: 14px;
        }
        .cart-item-qty {
          color: #64748b;
          font-size: 12px;
        }
        .cart-item-price {
          font-weight: 600;
          color: #11998e;
          font-size: 14px;
        }
        .cart-total {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: #f8fafc;
          border-top: 1px solid #e2e8f0;
        }
        .cart-total span:first-child {
          color: #64748b;
          font-size: 14px;
        }
        .cart-total-amount {
          font-size: 22px;
          font-weight: 700;
          color: #11998e;
        }
        .cart-actions {
          display: flex;
          gap: 8px;
          padding: 12px 16px;
          border-top: 1px solid #e2e8f0;
        }
        .cart-actions button {
          flex: 1;
          padding: 10px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .cart-actions button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .nav-active {
          background: #667eea !important;
          color: white !important;
        }
      `}</style>
    </div>
  );
};

export default Cashier;
