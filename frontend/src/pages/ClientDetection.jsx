import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useCamera from '../hooks/useCamera';
import { useKioskTimeout } from '../hooks/useKioskTimeout';
import { detectClothes, getProductByYoloClass, createSession, getOrCreateCartBySession, getCart, addCartItem, removeCartItem, submitCart, performLogout, extendSession } from '../services/api';
import '../styles/client-detection.css';

const STORAGE_KEY_SESSION = 'client_session_id';
const STORAGE_KEY_CART = 'client_cart_id';

const traducirCategoria = (className) => {
  if (!className) return 'Prenda';
  const productoMap = {
    'gorra-roja-lacoste': 'Gorra',
    'top': 'Camiseta',
    'pants': 'Pantalón'
  };
  return productoMap[className.toLowerCase()] || className;
};

const getDefaultSizes = (yoloClassName) => {
  const sizeMap = {
    'gorra-roja-lacoste': ['One Size'],
    'top': ['S', 'M', 'L', 'XL'],
    'pants': ['28', '30', '32', '34', '36']
  };
  return sizeMap[yoloClassName?.toLowerCase()] || ['S', 'M', 'L', 'XL'];
};

const extractSizesFromVariants = (variants) => {
  if (!variants || variants.length === 0) return null;
  const sizes = [...new Set(variants.map(v => v.size).filter(s => s))];
  return sizes.length > 0 ? sizes : null;
};

const ClientDetection = () => {
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imagen, setImagen] = useState(null);
  const [detections, setDetections] = useState(null);
  const [imageSize, setImageSize] = useState(null);
  const [error, setError] = useState('');
  const [carrito, setCarrito] = useState([]);
  const [mostrarCarrito, setMostrarCarrito] = useState(false);
  const [cartId, setCartId] = useState(null);
  const [_sessionId, setSessionId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showCountdown, setShowCountdown] = useState(false);
  const navigate = useNavigate();

  const handleKioskLogout = useCallback(async () => {
    localStorage.removeItem('client_session_id');
    localStorage.removeItem('client_cart_id');
    await performLogout();
    navigate('/');
  }, [navigate]);

  const { countdown, resetTimer } = useKioskTimeout(handleKioskLogout);

  useEffect(() => {
    if (countdown !== null) {
      setShowCountdown(true);
    } else {
      setShowCountdown(false);
    }
  }, [countdown]);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      let sessionId = localStorage.getItem(STORAGE_KEY_SESSION);
      let cartId = localStorage.getItem(STORAGE_KEY_CART);

      if (sessionId && cartId) {
        try {
          const existingCart = await getCart(cartId);
          if (existingCart && existingCart.status === 'building') {
            setSessionId(sessionId);
            setCartId(cartId);
            if (existingCart.items && existingCart.items.length > 0) {
              setCarrito(existingCart.items.map(item => ({
                name: item.product?.name || 'Producto',
                price: parseFloat(item.unit_price),
                brand: item.product?.category?.name || 'FashionCo',
                sku: item.product?.sku || 'N/A',
                tipoPrenda: traducirCategoria(item.product?.yolo_class_name),
                confidence: item.detection_confidence || 0,
                colors: [],
                sizes: [],
                yolo_class_name: item.product?.yolo_class_name || '',
                product_id: item.product_id,
                cartItemId: item.id
              })));
            }
            return;
          }
        } catch (err) {
          console.warn('Could not recover existing cart, creating new one:', err);
        }
      }

      const session = await createSession('client-detection-kiosk');
      sessionId = session.id;
      localStorage.setItem(STORAGE_KEY_SESSION, sessionId);

      const cart = await getOrCreateCartBySession(sessionId);
      cartId = cart.id;
      localStorage.setItem(STORAGE_KEY_CART, cartId);

      setSessionId(sessionId);
      setCartId(cartId);
    } catch (err) {
      console.error('Error initializing session/cart:', err);
      setError('Error al inicializar el sistema');
    }
  };

  const clearSession = () => {
    localStorage.removeItem(STORAGE_KEY_SESSION);
    localStorage.removeItem(STORAGE_KEY_CART);
    setSessionId(null);
    setCartId(null);
  };

  const {
    videoRef,
    isActive,
    error: cameraError,
    openCamera,
    closeCamera,
    captureFrame
  } = useCamera();

  const canvasRef = useRef(null);
  const resultCanvasRef = useRef(null);

  const processDetection = useCallback(async (imgData) => {
    setImagen(imgData);
    setError('');
    setLoading(true);
    setDetections(null);
    setProducto(null);

    try {
      const imgElement = new Image();
      imgElement.src = imgData;

      await new Promise((resolve) => {
        imgElement.onload = resolve;
      });

      const canvas = canvasRef.current;
      canvas.width = imgElement.width;
      canvas.height = imgElement.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(imgElement, 0, 0);

      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });

        try {
          const result = await detectClothes(file);

          if (result.detections && result.detections.length > 0) {
            const detection = result.detections[0];
            setDetections(result.detections);
            setImageSize(result.image_size);

            const dbProduct = await getProductByYoloClass(detection.class);

            if (dbProduct) {
              const variantSizes = extractSizesFromVariants(dbProduct.variants);
              const productoData = {
                name: dbProduct.name,
                price: parseFloat(dbProduct.base_price),
                brand: dbProduct.category?.name || 'FashionCo',
                sku: dbProduct.sku,
                tipoPrenda: traducirCategoria(detection.class),
                confidence: detection.confidence,
                colors: ['Rojo'],
                sizes: variantSizes || getDefaultSizes(detection.class),
                yolo_class_name: dbProduct.yolo_class_name,
                product_id: dbProduct.id
              };
              setProducto(productoData);
            } else {
              setProducto({
                name: detection.class,
                price: 0,
                brand: 'Desconocido',
                sku: 'N/A',
                tipoPrenda: traducirCategoria(detection.class),
                confidence: detection.confidence,
                colors: [],
                sizes: getDefaultSizes(detection.class),
                yolo_class_name: detection.class
              });
            }
          } else {
            setError('No se detectó una prenda. Intenta con otra imagen.');
          }
        } catch (err) {
          console.error('Error en detección:', err);
          setError('Error al procesar la imagen en el servidor');
        } finally {
          setLoading(false);
        }
      }, 'image/jpeg');

    } catch (err) {
      console.error('Error procesando imagen:', err);
      setError('Error al procesar la imagen');
      setLoading(false);
    }
  }, []);

  const handleCapture = useCallback(async () => {
    const canvas = canvasRef.current;
    const capturedImage = captureFrame(canvas);

    if (capturedImage) {
      closeCamera();
      try {
        await extendSession();
      } catch (err) {
        console.warn('Failed to extend session:', err);
      }
      processDetection(capturedImage);
    }
  }, [captureFrame, closeCamera, processDetection]);

  const agregarAlCarrito = async () => {
    if (!producto || !cartId) return;

    try {
      const newItem = await addCartItem(cartId, {
        product_id: producto.product_id,
        product_variant_id: null,
        quantity: 1,
        unit_price: producto.price,
        detection_confidence: producto.confidence
      });

      setCarrito(prev => [...prev, { ...producto, cartItemId: newItem.id }]);
      setProducto(null);
      setImagen(null);
      setDetections(null);
      try {
        await extendSession();
      } catch (err) {
        console.warn('Failed to extend session:', err);
      }
    } catch (err) {
      console.error('Error adding to cart:', err);
      setError('Error al agregar al carrito');
    }
  };

  const eliminarDelCarrito = async (cartItemId) => {
    try {
      await removeCartItem(cartId, cartItemId);
      setCarrito(prev => prev.filter(item => item.cartItemId !== cartItemId));
      try {
        await extendSession();
      } catch (err) {
        console.warn('Failed to extend session:', err);
      }
    } catch (err) {
      console.error('Error removing from cart:', err);
      setError('Error al eliminar del carrito');
    }
  };

  const totalesCarrito = () => {
    const total = carrito.reduce((sum, item) => sum + item.price, 0);
    return { items: carrito.length, total };
  };

  const enviarAlAdmin = async () => {
    if (carrito.length === 0 || !cartId) return;

    try {
      setSubmitting(true);
      await submitCart(cartId);
      setCarrito([]);
      alert('¡Pedido enviado a caja! Un administrador lo procesará pronto.');
      clearSession();
      const session = await createSession('client-detection-kiosk');
      localStorage.setItem(STORAGE_KEY_SESSION, session.id);
      setSessionId(session.id);
      const newCart = await getOrCreateCartBySession(session.id);
      localStorage.setItem(STORAGE_KEY_CART, newCart.id);
      setCartId(newCart.id);
    } catch (err) {
      console.error('Error submitting cart:', err);
      setError('Error al enviar el pedido');
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setProducto(null);
    setImagen(null);
    setDetections(null);
    setImageSize(null);
    setError('');
  };

  const drawBoundingBoxes = useCallback(() => {
    if (!imagen || !detections || detections.length === 0 || !resultCanvasRef.current) {
      return;
    }

    const canvas = resultCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const imgEl = new Image();

    imgEl.onload = () => {
      canvas.width = imgEl.naturalWidth;
      canvas.height = imgEl.naturalHeight;
      ctx.drawImage(imgEl, 0, 0);

      const [imgW, imgH] = imageSize || [imgEl.naturalWidth, imgEl.naturalHeight];

      detections.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const scaleX = canvas.width / imgW;
        const scaleY = canvas.height / imgH;

        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const sx2 = x2 * scaleX;
        const sy2 = y2 * scaleY;

        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        const label = `${det.class.toUpperCase()} ${Math.round(det.confidence * 100)}%`;
        ctx.font = 'bold 14px sans-serif';
        const textMetrics = ctx.measureText(label);
        ctx.fillRect(sx1, sy1 - 24, textMetrics.width + 12, 22);
        ctx.fillStyle = '#00ff00';
        ctx.fillText(label, sx1 + 6, sy1 - 8);
      });
    };
    imgEl.src = imagen;
  }, [imagen, detections, imageSize]);

  useEffect(() => {
    drawBoundingBoxes();
  }, [drawBoundingBoxes]);

  const finalError = cameraError || error;

  return (
    <div className="client-page">
      <header className="client-header">
        <div className="logo">
          <span className="logo-icon">👕</span>
          FashionVision
        </div>
        <div className="header-actions">
          <button
            className="btn-carrito"
            onClick={() => setMostrarCarrito(!mostrarCarrito)}
          >
            🛒 Carrito
            {carrito.length > 0 && (
              <span className="carrito-badge">{carrito.length}</span>
            )}
          </button>

        </div>
      </header>

      {mostrarCarrito && (
        <div className="carrito-panel">
          <div className="carrito-header">
            <h3>Mi Carrito ({totalesCarrito().items} prendas)</h3>
            <button onClick={() => setMostrarCarrito(false)}>✕</button>
          </div>
          <div className="carrito-items">
            {carrito.length === 0 ? (
              <p className="carrito-vacio">Tu carrito está vacío</p>
            ) : (
              carrito.map((item) => (
                <div key={item.cartItemId} className="carrito-item">
                  <div className="item-info">
                    <span className="item-name">{item.name}</span>
                    <span className="item-price">${item.price.toFixed(2)}</span>
                  </div>
                  <button
                    className="btn-eliminar"
                    onClick={() => eliminarDelCarrito(item.cartItemId)}
                  >
                    🗑️
                  </button>
                </div>
              ))
            )}
          </div>
          {carrito.length > 0 && (
            <div className="carrito-footer">
              <div className="carrito-total">
                <span>Total:</span>
                <span className="total-amount">${totalesCarrito().total.toFixed(2)}</span>
              </div>
              <button className="btn-enviar" onClick={enviarAlAdmin} disabled={submitting}>
                {submitting ? 'Enviando...' : 'Enviar a Caja'}
              </button>
            </div>
          )}
        </div>
      )}

      <main className="client-main">
        <div className="detection-container">
          <h1 className="page-title">Encuentra tu Prenda Ideal</h1>
          <p className="page-subtitle">
            Usa la cámara para detectar prendas y agregarlas a tu carrito
          </p>

          {finalError && <div className="error-message">{finalError}</div>}

          <div className="button-section">
            {!isActive && !imagen && (
              <button className="btn-primary" onClick={async () => {
                try {
                  await extendSession();
                } catch (err) {
                  console.warn('Failed to extend session:', err);
                }
                openCamera();
              }}>
                <span>📷</span> Abrir Cámara
              </button>
            )}
          </div>

          <canvas ref={canvasRef} style={{ display: 'none' }} />

          {isActive && (
            <div className="camera-view">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="camera-video"
              />
              <div className="camera-controls">
                <button className="btn-capture" onClick={handleCapture}>
                  <span>⏺</span> Capturar
                </button>
                <button className="btn-cancel" onClick={closeCamera}>
                  ✕ Cerrar
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="processing-view">
              <div className="spinner"></div>
              <p>Analizando imagen...</p>
              <p className="processing-text">Buscando prendas en la imagen</p>
            </div>
          )}

          {imagen && !loading && (
            <div className="result-view">
              <div className="result-image-container">
                <img src={imagen} alt="Capturada" className="result-image" />
                {detections && detections.length > 0 && (
                  <canvas ref={resultCanvasRef} className="result-canvas-overlay" />
                )}
              </div>

              {producto ? (
                <div className="product-info-card">
                  <div className="product-badge">{producto.tipoPrenda}</div>
                  <h2 className="product-name">{producto.name}</h2>
                  <p className="product-brand">{producto.brand}</p>

                  <div className="price-tag">
                    <span className="price">${producto.price.toFixed(2)}</span>
                  </div>

                  <div className="product-details">
                    <div className="detail-row">
                      <span className="detail-label">SKU</span>
                      <span className="detail-value">{producto.sku}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Confianza</span>
                      <span className="detail-value confidence">
                        {(producto.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {producto.sizes && producto.sizes.length > 0 && (
                    <div className="tags-section">
                      <span className="tags-label">Tallas</span>
                      <div className="tags-list">
                        {producto.sizes.map(s => (
                          <span key={s} className="tag">{s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {producto.colors && producto.colors.length > 0 && (
                    <div className="tags-section">
                      <span className="tags-label">Colores</span>
                      <div className="tags-list">
                        {producto.colors.map(c => (
                          <span key={c} className="tag">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="action-buttons">
                    <button className="btn-add-cart" onClick={agregarAlCarrito}>
                      🛒 Agregar al Carrito
                    </button>
                    <button className="btn-reset" onClick={reset}>
                      🔄 Nueva Captura
                    </button>
                  </div>
                </div>
              ) : (
                <div className="no-detection">
                  <h3>No se detectó ninguna prenda</h3>
                  <p>Intenta con mejor iluminación o acerca la prenda a la cámara</p>
                  <button className="btn-reset" onClick={reset}>
                    🔄 Intentar de nuevo
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      <footer className="client-footer">
        <p>FashionVision AI - Sistema de Detección de Prendas</p>
      </footer>

      {showCountdown && countdown !== null && (
        <div className="countdown-overlay">
          <div className="countdown-modal">
            <h2 className="countdown-title">Tu sesión está por terminar</h2>
            <p className="countdown-subtitle">¿Deseas continuar?</p>
            <div className="countdown-number">{countdown}</div>
            <p className="countdown-text">segundos</p>
            <button className="btn-keep-session" onClick={resetTimer}>
              Mantener sesión
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientDetection;
