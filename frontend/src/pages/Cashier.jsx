import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { performLogout } from '../services/api';
import { getPendingCarts, approveCart, rejectCart, processPayment, posInitializePayment, posWaitForCard, posProcessPayment, posCancelTransaction, posCompletePayment } from '../services/api';
import { formatLocalDateTime } from '../utils/dateUtils';
import '../styles/home.css';

const Cashier = () => {
  const [carts, setCarts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [selectedCart, setSelectedCart] = useState(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('cash');
  const [receiptData, setReceiptData] = useState(null);
  const [posPayment, setPosPayment] = useState(null);
  const [posStatus, setPosStatus] = useState('');
  const [posLogs, setPosLogs] = useState([]);
  const navigate = useNavigate();

  const addPosLog = (message) => {
    setPosLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message }]);
  };

  const handleLogout = () => {
    performLogout();
    navigate('/');
  };

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

  const openPaymentModal = (cart) => {
    setSelectedCart(cart);
    setSelectedPaymentMethod('cash');
    setShowPaymentModal(true);
  };

  const closePaymentModal = () => {
    setShowPaymentModal(false);
    setSelectedCart(null);
    setSelectedPaymentMethod('cash');
  };

  const handlePayment = async () => {
    if (!selectedCart) return;

    if (selectedPaymentMethod === 'card') {
      await handlePosPayment();
      return;
    }

    try {
      setProcessingId(selectedCart.id);
      const result = await processPayment(selectedCart.id, selectedPaymentMethod);

      if (result.receipt) {
        setReceiptData(result.receipt.receipt_data);
        setShowReceiptModal(true);
      }

      closePaymentModal();
      await fetchPendingCarts();
    } catch (err) {
      setError('Error al procesar pago');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  const handlePosPayment = async () => {
    if (!selectedCart) return;

    try {
      setProcessingId(selectedCart.id);
      setPosLogs([]);
      addPosLog('Iniciando pago con terminal...');

      const cartTotal = selectedCart.total || 0;
      const initResult = await posInitializePayment(selectedCart.id, cartTotal);

      if (!initResult.success) {
        addPosLog('Error: No se pudo inicializar el terminal');
        return;
      }

      const transactionId = initResult.transaction_id;
      setPosPayment({ transactionId, amount: cartTotal });
      setPosStatus('waiting_card');
      addPosLog(`Terminal listo. Transaction ID: ${transactionId}`);
      addPosLog('Esperando tarjeta...');

      const waitResult = await posWaitForCard(transactionId);

      if (!waitResult.success) {
        setPosStatus('timeout');
        addPosLog('Error: Tarjeta no detectada');
        await new Promise(resolve => setTimeout(resolve, 2000));
        setPosPayment(null);
        setProcessingId(null);
        return;
      }

      setPosStatus('processing');
      addPosLog('Tarjeta detectada. Procesando...');

      const processResult = await posProcessPayment(transactionId);
      setPosStatus(processResult.status);

      if (processResult.status === 'approved') {
        addPosLog(`Pago aprobado. Auth: ${processResult.authorization_code}`);
        addPosLog('Completando transacción en sistema...');

        const completeResult = await posCompletePayment(transactionId, selectedCart.id);

        if (completeResult.success) {
          setReceiptData(completeResult.receipt);
          addPosLog('Transacción completada exitosamente');
          setShowReceiptModal(true);
          await fetchPendingCarts();
        } else {
          addPosLog('Error al completar transacción');
        }
      } else if (processResult.status === 'declined') {
        addPosLog(`Pago rechazado: ${processResult.error_message}`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      } else {
        addPosLog(`Error: ${processResult.error_message}`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }

      setPosPayment(null);
      closePaymentModal();

    } catch (err) {
      setError('Error en el pago con terminal');
      console.error(err);
      addPosLog(`Error: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleCancelPosPayment = async () => {
    if (posPayment) {
      try {
        await posCancelTransaction(posPayment.transactionId);
        addPosLog('Transacción cancelada');
      } catch (err) {
        console.error(err);
      }
      setPosPayment(null);
      setPosStatus('');
    }
    setProcessingId(null);
  };

  const closeReceiptModal = () => {
    setShowReceiptModal(false);
    setReceiptData(null);
  };

  return (
    <div className="home-page">
      <header>
        <div className="logo">💰 Caja - FashionVision</div>
        <nav>
          <button className="nav-active">Caja</button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
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
                  <span className="cart-date">{formatLocalDateTime(cart.created_at)}</span>
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
                      onClick={() => openPaymentModal(cart)}
                      disabled={processingId === cart.id}
                    >
                      💳 Cobrar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showPaymentModal && selectedCart && (
        <div className="modal-overlay" onClick={closePaymentModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>💳 Seleccionar Método de Pago</h3>
              <button className="modal-close" onClick={closePaymentModal}>✕</button>
            </div>

            <div className="modal-body">
              <div className="cart-summary">
                <p><strong>Pedido:</strong> #{selectedCart.id.slice(0, 8).toUpperCase()}</p>
                <p><strong>Total a pagar:</strong> <span className="total-amount">${selectedCart.total?.toFixed(2) || '0.00'}</span></p>
              </div>

              {posPayment ? (
                <div className="pos-status-panel">
                  <h4>Estado del Terminal</h4>
                  <div className={`pos-status-indicator ${posStatus}`}>
                    {posStatus === 'waiting_card' && '⏳ Esperando tarjeta...'}
                    {posStatus === 'processing' && '🔄 Procesando...'}
                    {posStatus === 'approved' && '✅ Aprobado'}
                    {posStatus === 'declined' && '❌ Rechazado'}
                    {posStatus === 'timeout' && '⏱️ Timeout'}
                    {posStatus === 'cancelled' && '🚫 Cancelado'}
                  </div>
                  <div className="pos-logs">
                    {posLogs.map((log, idx) => (
                      <div key={idx} className="pos-log-entry">
                        <span className="log-time">[{log.time}]</span>
                        <span className="log-message">{log.message}</span>
                      </div>
                    ))}
                  </div>
                  <button className="btn-outline" onClick={handleCancelPosPayment}>
                    Cancelar
                  </button>
                </div>
              ) : (
                <>
                  <div className="payment-methods">
                    <h4>Método de pago</h4>
                    <div className="method-options">
                      <label className={`method-option ${selectedPaymentMethod === 'cash' ? 'selected' : ''}`}>
                        <input
                          type="radio"
                          name="paymentMethod"
                          value="cash"
                          checked={selectedPaymentMethod === 'cash'}
                          onChange={() => setSelectedPaymentMethod('cash')}
                        />
                        <span className="method-icon">💵</span>
                        <span className="method-name">Efectivo</span>
                      </label>
                      <label className={`method-option ${selectedPaymentMethod === 'card' ? 'selected' : ''}`} title="Pago con terminal POS">
                        <input
                          type="radio"
                          name="paymentMethod"
                          value="card"
                          checked={selectedPaymentMethod === 'card'}
                          onChange={() => setSelectedPaymentMethod('card')}
                        />
                        <span className="method-icon">💳</span>
                        <span className="method-name">Terminal POS</span>
                      </label>
                    </div>
                  </div>

                  <div className="modal-footer">
                    <button className="btn-outline" onClick={closePaymentModal}>
                      Cancelar
                    </button>
                    <button className="btn-primary" onClick={handlePayment}>
                      Confirmar Pago
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {showReceiptModal && receiptData && (
        <div className="modal-overlay" onClick={closeReceiptModal}>
          <div className="modal-content receipt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header receipt-header">
              <h3>✅ Pago Completado</h3>
              <button className="modal-close" onClick={closeReceiptModal}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="receipt-business">
                <h4>FashionVision AI</h4>
                <p>Recibo de Pago</p>
              </div>

              <div className="receipt-info">
                <p><strong>No. Receipt:</strong> {receiptData.receipt_number}</p>
                <p><strong>No. Order:</strong> {receiptData.order_number}</p>
                <p><strong>Fecha:</strong> {formatLocalDateTime(receiptData.created_at)}</p>
                <p><strong>Método:</strong> {receiptData.payment_method === 'cash' ? '💵 Efectivo' : '💳 Tarjeta'}</p>
              </div>

              <div className="receipt-items">
                <h4>Artículos</h4>
                {receiptData.items && receiptData.items.map((item, idx) => (
                  <div key={idx} className="receipt-item">
                    <span>{item.quantity}x {item.name}</span>
                    <span>${item.subtotal.toFixed(2)}</span>
                  </div>
                ))}
              </div>

              <div className="receipt-totals">
                <div className="receipt-row">
                  <span>Subtotal:</span>
                  <span>${receiptData.subtotal?.toFixed(2)}</span>
                </div>
                <div className="receipt-row">
                  <span>IVA (16%):</span>
                  <span>${receiptData.tax_amount?.toFixed(2)}</span>
                </div>
                <div className="receipt-row total">
                  <span>Total:</span>
                  <span>${receiptData.total_amount?.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-primary" onClick={closeReceiptModal}>
                Aceptar
              </button>
            </div>
          </div>
        </div>
      )}

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

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        .modal-content {
          background: white;
          border-radius: 16px;
          width: 90%;
          max-width: 400px;
          overflow: hidden;
        }
        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        .modal-header h3 {
          margin: 0;
          font-size: 18px;
        }
        .modal-close {
          background: none;
          border: none;
          color: white;
          font-size: 20px;
          cursor: pointer;
          padding: 4px 8px;
        }
        .modal-body {
          padding: 20px;
        }
        .cart-summary {
          background: #f8fafc;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .cart-summary p {
          margin: 8px 0;
          color: #64748b;
        }
        .cart-summary .total-amount {
          font-size: 24px;
          font-weight: 700;
          color: #11998e;
        }
        .payment-methods h4 {
          margin: 0 0 12px 0;
          color: #1e293b;
        }
        .method-options {
          display: flex;
          gap: 12px;
        }
        .method-option {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .method-option:hover {
          border-color: #667eea;
        }
        .method-option.selected {
          border-color: #667eea;
          background: #f0f3ff;
        }
        .method-option input {
          display: none;
        }
        .method-icon {
          font-size: 32px;
          margin-bottom: 8px;
        }
        .method-name {
          font-weight: 600;
          color: #1e293b;
        }
        .method-option.disabled {
          opacity: 0.5;
          cursor: not-allowed;
          border-color: #cbd5e1;
          background: #f1f5f9;
        }
        .method-option.disabled:hover {
          border-color: #cbd5e1;
        }
        .disabled-label {
          font-size: 11px;
          color: #ef4444;
          margin-top: 4px;
          font-weight: 500;
        }
        .modal-footer {
          display: flex;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid #e2e8f0;
        }
        .modal-footer button {
          flex: 1;
          padding: 12px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        /* Receipt Modal Styles */
        .receipt-modal {
          max-width: 350px;
        }
        .receipt-header {
          background: linear-gradient(135deg, #11998e 0%, #0d7a6f 100%);
        }
        .receipt-business {
          text-align: center;
          margin-bottom: 16px;
        }
        .receipt-business h4 {
          margin: 0;
          font-size: 18px;
          color: #1e293b;
        }
        .receipt-business p {
          margin: 4px 0 0 0;
          color: #64748b;
          font-size: 14px;
        }
        .receipt-info {
          background: #f8fafc;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 16px;
        }
        .receipt-info p {
          margin: 4px 0;
          font-size: 13px;
          color: #64748b;
        }
        .receipt-items {
          margin-bottom: 16px;
        }
        .receipt-items h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #1e293b;
          border-bottom: 1px solid #e2e8f0;
          padding-bottom: 8px;
        }
        .receipt-item {
          display: flex;
          justify-content: space-between;
          padding: 4px 0;
          font-size: 13px;
          color: #64748b;
        }
        .receipt-totals {
          border-top: 1px dashed #e2e8f0;
          padding-top: 12px;
        }
        .receipt-row {
          display: flex;
          justify-content: space-between;
          padding: 4px 0;
          font-size: 14px;
          color: #64748b;
        }
        .receipt-row.total {
          font-weight: 700;
          font-size: 18px;
          color: #11998e;
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #e2e8f0;
        }
      `}</style>
    </div>
  );
};

export default Cashier;
