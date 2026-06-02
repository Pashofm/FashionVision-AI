import React, { useState, useRef, useCallback, useEffect } from 'react';
import useCamera from '../hooks/useCamera';
import useRealTimeDetection from '../hooks/useRealTimeDetection';
import useAutoDetection from '../hooks/useAutoDetection';
import useProductTabs from '../hooks/useProductTabs';
import { useKioskTimeout } from '../hooks/useKioskTimeout';
import CameraSection from '../components/CameraSection';
import CountdownOverlay from '../components/CountdownOverlay';
import LiveBboxOverlay from '../components/LiveBboxOverlay';
import ProductTabs from '../components/ProductTabs';
import ProductTabPanel from '../components/ProductTabPanel';
import { detectClothes, getDetectionProductById, searchProductVariant, createSession, getOrCreateCartBySession, getCart, addCartItem, removeCartItem, submitCart, extendSession } from '../services/api';
import '../styles/client-detection.css';

const STORAGE_KEY_SESSION = 'client_session_id';
const STORAGE_KEY_CART = 'client_cart_id';

const ClientDetection = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [carrito, setCarrito] = useState([]);
  const [mostrarCarrito, setMostrarCarrito] = useState(false);
  const [cartId, setCartId] = useState(null);
  const [_sessionId, setSessionId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [isCaptureComplete, setIsCaptureComplete] = useState(false);
  const [kioskIdle, setKioskIdle] = useState(true);

  const handleKioskLogout = useCallback(() => {
    localStorage.removeItem('client_session_id');
    localStorage.removeItem('client_cart_id');
    setKioskIdle(true);
  }, []);

  const { countdown: kioskCountdown, resetTimer } = useKioskTimeout(handleKioskLogout, !kioskIdle);
  const [showKioskCountdown, setShowKioskCountdown] = useState(false);

  useEffect(() => {
    setShowKioskCountdown(kioskCountdown !== null);
  }, [kioskCountdown]);

  const initSession = async () => {
    try {
      let sessionId = localStorage.getItem(STORAGE_KEY_SESSION);
      let cartIdStorage = localStorage.getItem(STORAGE_KEY_CART);

      if (sessionId && cartIdStorage) {
        try {
          const existingCart = await getCart(cartIdStorage);
          if (existingCart && existingCart.status === 'building') {
            setSessionId(sessionId);
            setCartId(cartIdStorage);
            if (existingCart.items && existingCart.items.length > 0) {
              setCarrito(existingCart.items.map(item => ({
                name: item.product?.name || 'Producto',
                price: parseFloat(item.unit_price),
                brand: item.product?.category?.name || 'FashionCo',
                sku: item.product?.sku || 'N/A',
                tipoPrenda: item.product?.category?.name || 'Prenda',
                confidence: item.detection_confidence || 0,
                colors: [],
                sizes: [],
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
      cartIdStorage = cart.id;
      localStorage.setItem(STORAGE_KEY_CART, cartIdStorage);

      setSessionId(sessionId);
      setCartId(cartIdStorage);
    } catch (err) {
      console.error('Error initializing session/cart:', err);
      setError('Error al inicializar el sistema');
    }
  };

  const handleStartCapture = async () => {
    setKioskIdle(false);
    await initSession();
  };

  const {
    videoRef,
    isActive,
    error: cameraError,
    openCamera,
    closeCamera,
    captureFrame
  } = useCamera();

  const {
    lastDetections,
    startDetection,
    stopDetection
  } = useRealTimeDetection();

  const {
    status: detectionStatus,
    countdown,
    message: countdownMessage,
    startAutoDetection,
    cancelAutoDetection,
    pauseDetection: pauseAutoDetection,
    resetFromPause,
    onFirstDetection,
    onProcessingComplete
  } = useAutoDetection(handleCaptureTriggered);

  const {
    products,
    activeTabIndex,
    activeProduct,
    addProduct,
    removeProduct,
    setActiveTab,
    selectSize,
    selectColor,
    setMatchingVariant,
    canAddToCart,
    updateProductImage,
    clearAllProducts
  } = useProductTabs();

  const canvasRef = useRef(null);
  const resultCanvasRef = useRef(null);
  const lastDetectionRef = useRef([]);

  async function handleCaptureTriggered() {
    setIsCaptureComplete(true);
    const canvas = canvasRef.current;
    const capturedImage = captureFrame(canvas);

    if (capturedImage) {
      stopDetection();
      pauseAutoDetection();
      await processDetection(capturedImage);
    }
  }

  const processDetection = useCallback(async (imgData) => {
    setLoading(true);
    setError('');

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
            for (const detection of result.detections) {
              let productData = null;
              let matchSource = 'none';
              let matchSimilarity = null;

              if (detection.catalog_match && detection.catalog_match.product_id) {
                productData = await getDetectionProductById(detection.catalog_match.product_id);
                if (productData) {
                  matchSource = 'clip';
                  matchSimilarity = detection.catalog_match.similarity;
                }
              }

              if (productData) {
                const productoData = {
                  name: productData.name,
                  price: parseFloat(productData.base_price),
                  brand: productData.category_name || 'FashionCo',
                  sku: productData.sku,
                  tipoProducto: traducirCategoria(detection.class),
                  confidence: detection.confidence,
                  colors: productData.colors.map(c => ({ id: c.attribute_id, name: c.value, hex: c.hex_code, stock: c.stock })),
                  sizes: productData.sizes.map(s => ({ id: s.attribute_id, name: s.value, stock: s.stock })),
                  product_id: productData.id,
                  bbox: detection.bbox,
                  imageData: imgData,
                  matchSource: matchSource,
                  matchSimilarity: matchSimilarity,
                  catalog_match: detection.catalog_match || null,
                };

                const addResult = addProduct(productoData);

                if (addResult.success && !addResult.isUpdate && addResult.productId) {
                  updateProductImage(addResult.productId, imgData);
                }
              } else {
                const productoData = {
                  name: detection.class,
                  price: 0,
                  brand: 'Desconocido',
                  sku: 'N/A',
                  tipoProducto: traducirCategoria(detection.class),
                  confidence: detection.confidence,
                  colors: getDefaultColors(detection.class).map(c => ({ name: c, hex: null, stock: 0 })),
                  sizes: getDefaultSizes(detection.class).map(s => ({ name: s, stock: 0 })),
                  bbox: detection.bbox,
                  imageData: imgData,
                  matchSource: 'none',
                  matchSimilarity: null,
                  catalog_match: null,
                };

                addProduct(productoData);
              }
            }
          } else {
            setError('No se detectó una prenda. Intenta con otra imagen.');
            setIsCaptureComplete(false);
          }
        } catch (err) {
          console.error('Error en detección:', err);
          setError('Error al procesar la imagen en el servidor');
        } finally {
          setLoading(false);
          setIsCaptureComplete(true);
          closeCamera();
          onProcessingComplete();
        }
      }, 'image/jpeg');

    } catch (err) {
      console.error('Error procesando imagen:', err);
      setError('Error al procesar la imagen');
      setLoading(false);
      setIsCaptureComplete(false);
      onProcessingComplete();
    }
  }, [addProduct, updateProductImage, onProcessingComplete]);

  useEffect(() => {
    if (lastDetections.length > 0) {
      const currentDetections = lastDetections.map(d => `${d.class}-${d.bbox.join(',')}`).join('|');
      const lastDetectionsStr = lastDetectionRef.current.map(d => `${d.class}-${d.bbox.join(',')}`).join('|');

      if (currentDetections !== lastDetectionsStr) {
        lastDetectionRef.current = lastDetections;

        if (detectionStatus === 'detecting' && lastDetections.length > 0) {
          onFirstDetection();
        }
      }
    }
  }, [lastDetections, detectionStatus, onFirstDetection, lastDetectionRef]);

  useEffect(() => {
    if (isActive && !isCaptureComplete && (detectionStatus === 'idle' || detectionStatus === 'paused')) {
      startDetection(videoRef);
      if (detectionStatus === 'idle') {
        startAutoDetection();
      }
    }
  }, [isActive, detectionStatus, isCaptureComplete, startDetection, startAutoDetection, videoRef]);

  const handleOpenCamera = async () => {
    try {
      await extendSession();
    } catch (err) {
      console.warn('Failed to extend session:', err);
    }
    await openCamera();
  };

  const handleCloseCamera = () => {
    stopDetection();
    cancelAutoDetection();
    closeCamera();
    clearAllProducts();
    lastDetectionRef.current = [];
    setIsCaptureComplete(false);
  };

  const handleSizeSelect = useCallback(async (productId, size) => {
    selectSize(productId, size);
    const product = products.find(p => p.id === productId);
    if (product?.selectedColor && product?.product_id) {
      try {
        const variant = await searchProductVariant(product.product_id, size.id, product.selectedColor.id);
        if (!variant || variant.quantity_available <= 0) {
          setMatchingVariant(productId, null);
        } else {
          setMatchingVariant(productId, variant);
        }
      } catch (err) {
        console.error('Error searching variant:', err);
        setMatchingVariant(productId, null);
      }
    }
  }, [selectSize, setMatchingVariant]);

  const handleColorSelect = useCallback(async (productId, color) => {
    selectColor(productId, color);
    const product = products.find(p => p.id === productId);
    if (product?.selectedSize && product?.product_id) {
      try {
        const variant = await searchProductVariant(product.product_id, product.selectedSize.id, color.id);
        if (!variant || variant.quantity_available <= 0) {
          setMatchingVariant(productId, null);
        } else {
          setMatchingVariant(productId, variant);
        }
      } catch (err) {
        console.error('Error searching variant:', err);
        setMatchingVariant(productId, null);
      }
    }
  }, [selectColor, setMatchingVariant, products]);

  const handleAddToCart = async (productId) => {
    const product = products.find(p => p.id === productId);
    if (!product || !cartId || !canAddToCart(productId)) return;

    try {
      const newItem = await addCartItem(cartId, {
        product_id: product.product_id,
        product_variant_id: product.matchingVariant.variant_id,
        quantity: 1,
        unit_price: product.precio,
        detection_confidence: product.confidence
      });

      setCarrito(prev => [...prev, { ...product, price: product.precio, cartItemId: newItem.id }]);
      removeProduct(productId);

      const remainingProducts = products.length - 1;

      if (remainingProducts === 0) {
        stopDetection();
        cancelAutoDetection();
        closeCamera();
        resetFromPause();
        lastDetectionRef.current = [];
        setIsCaptureComplete(false);
      }

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

  const handleRemoveProduct = (productId) => {
    removeProduct(productId);

    if (products.length <= 1) {
      stopDetection();
      cancelAutoDetection();
      closeCamera();
      resetFromPause();
      lastDetectionRef.current = [];
      setIsCaptureComplete(false);
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
      localStorage.removeItem(STORAGE_KEY_SESSION);
      localStorage.removeItem(STORAGE_KEY_CART);
      setKioskIdle(true);
    } catch (err) {
      console.error('Error submitting cart:', err);
      setError('Error al enviar el pedido');
    } finally {
      setSubmitting(false);
    }
  };

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
      'accessories': ['One Size'],
      'clothing': ['S', 'M', 'L', 'XL'],
      'shoes': ['25', '26', '27', '28', '29'],
      'bags': ['One Size']
    };
    return sizeMap[yoloClassName?.toLowerCase()] || ['S', 'M', 'L', 'XL'];
  };

  const getDefaultColors = (yoloClassName) => {
    const colorMap = {
      'accessories': ['Unico'],
      'clothing': ['Blanco', 'Negro', 'Azul'],
      'shoes': ['Negro', 'Blanco', 'Marrón'],
      'bags': ['Unico']
    };
    return colorMap[yoloClassName?.toLowerCase()] || ['Unico'];
  };

  const drawBoundingBoxes = useCallback(() => {
    if (!activeProduct?.imageData || !products || products.length === 0 || !resultCanvasRef.current) {
      return;
    }

    const canvas = resultCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const imgEl = new Image();

    imgEl.onload = () => {
      canvas.width = imgEl.naturalWidth;
      canvas.height = imgEl.naturalHeight;
      ctx.drawImage(imgEl, 0, 0);

      const imageSize = activeProduct.imageData ? [imgEl.naturalWidth, imgEl.naturalHeight] : [imgEl.naturalWidth, imgEl.naturalHeight];

      products.forEach((product, idx) => {
        if (!product.bbox) return;

        const [x1, y1, x2, y2] = product.bbox;
        const scaleX = canvas.width / imageSize[0];
        const scaleY = canvas.height / imageSize[1];

        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const sx2 = x2 * scaleX;
        const sy2 = y2 * scaleY;

        const isActive = idx === activeTabIndex;

        ctx.strokeStyle = isActive ? '#00ff88' : '#00ff00';
        ctx.lineWidth = isActive ? 3 : 2;
        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';

        const matchIndicator = product.matchSource === 'clip' ? ' ✓' : '';
        const label = `${product.tipoProducto?.toUpperCase() || 'ITEM'} ${Math.round((product.confidence || 0) * 100)}%${matchIndicator}`;
        ctx.font = 'bold 14px sans-serif';
        const textMetrics = ctx.measureText(label);
        ctx.fillRect(sx1, sy1 - 24, textMetrics.width + 12, 22);

        ctx.fillStyle = isActive ? '#00ff88' : '#00ff00';
        ctx.fillText(label, sx1 + 6, sy1 - 8);
      });
    };
    imgEl.src = activeProduct.imageData || activeProduct?.imageData;
  }, [activeProduct, products, activeTabIndex]);

  useEffect(() => {
    drawBoundingBoxes();
  }, [drawBoundingBoxes]);

  const finalError = cameraError || error;

  if (kioskIdle) {
    return (
      <div className="kiosk-page">
        <div className="kiosk-container">
          <div className="kiosk-header">
            <span className="kiosk-icon">👕</span>
            <h1>FashionVision</h1>
            <p>Sistema Kiosko de Detección de Prendas</p>
          </div>

          <button className="kiosk-start-btn" onClick={handleStartCapture}>
            <span className="btn-icon">📷</span>
            Iniciar Captura
          </button>

          <p className="kiosk-hint">
            Toca el botón para comenzar a detectar prendas
          </p>
        </div>
      </div>
    );
  }

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
            {!isActive && products.length === 0 && !isCaptureComplete && (
              <button className="btn-primary" onClick={handleOpenCamera}>
                <span>📷</span> Abrir Cámara
              </button>
            )}
          </div>

          <canvas ref={canvasRef} style={{ display: 'none' }} />

          {isActive && (
            <div className="camera-view">
              <div className="camera-video-wrapper">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="camera-video"
                />
                <LiveBboxOverlay
                  videoRef={videoRef}
                  detections={lastDetections}
                  activeIndices={products.map((p, i) => i)}
                />
              </div>
              <CameraSection
                isActive={isActive}
                onClose={handleCloseCamera}
              />
            </div>
          )}

          {loading && (
            <div className="processing-view">
              <div className="spinner"></div>
              <p>Analizando imagen...</p>
              <p className="processing-text">Buscando prendas en la imagen</p>
            </div>
          )}

{isCaptureComplete && products.length > 0 && !loading && (
            <div className="products-panel">
              {activeProduct?.imageData && (
                <div className="result-image-container">
                  <img src={activeProduct.imageData} alt="Capturada" className="result-image" />
                  <canvas ref={resultCanvasRef} className="result-canvas-overlay" />
                </div>
              )}

              <ProductTabs
                products={products}
                activeTabIndex={activeTabIndex}
                onSelectTab={setActiveTab}
                onRemoveTab={handleRemoveProduct}
              />

              {activeProduct && (
                <div className="product-info-layout">
                  <div className="product-info-left">
                    <div className="product-main-info">
                      <span className="product-badge">{activeProduct.tipoProducto}</span>
                      <h2 className="product-name">{activeProduct.name}</h2>
                      <p className="product-brand">{activeProduct.marca}</p>
                      <div className="price-tag">
                        <span className="price">${activeProduct.precio?.toFixed(2) || '0.00'}</span>
                      </div>
                    </div>

                    <div className="product-details">
                      <div className="detail-row">
                        <span className="detail-label">SKU</span>
                        <span className="detail-value">{activeProduct.sku}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Confianza</span>
                        <span className="detail-value confidence">
                          {((activeProduct.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="product-info-right">
                    {activeProduct.sizes && activeProduct.sizes.length > 0 && (
                      <div className="tags-section">
                        <span className="tags-label">Tallas</span>
                        <div className="tags-list">
                          {activeProduct.sizes.map((s, idx) => (
                            <button
                              key={`size-${idx}`}
                              className={`tag ${activeProduct.selectedSize?.id === s.id || activeProduct.selectedSize?.name === s.name ? 'selected' : ''} ${s.stock === 0 ? 'out-of-stock' : ''}`}
                              onClick={() => s.stock > 0 && handleSizeSelect(activeProduct.id, s)}
                              disabled={s.stock === 0}
                            >
                              {s.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeProduct.colors && activeProduct.colors.length > 0 && (
                      <div className="tags-section">
                        <span className="tags-label">Colores</span>
                        <div className="tags-list">
                          {activeProduct.colors.map((c, idx) => (
                            <button
                              key={`color-${idx}`}
                              className={`tag ${activeProduct.selectedColor?.id === c.id || activeProduct.selectedColor?.name === c.name ? 'selected' : ''} ${c.stock === 0 ? 'out-of-stock' : ''}`}
                              onClick={() => c.stock > 0 && handleColorSelect(activeProduct.id, c)}
                              disabled={c.stock === 0}
                            >
                              {c.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeProduct.selectionError && (
                      <div className="selection-error">
                        {activeProduct.selectionError}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeProduct && (
                <div className="product-action-footer">
                  <button
                    className="btn-add-cart-full"
                    onClick={() => handleAddToCart(activeProduct.id)}
                    disabled={!canAddToCart(activeProduct.id)}
                  >
                    🛒 Agregar al Carrito
                  </button>
                  <button
                    className="btn-remove-product"
                    onClick={() => handleRemoveProduct(activeProduct.id)}
                  >
                    ✕ Eliminar
                  </button>
                </div>
              )}
            </div>
          )}

          {loading && (
            <div className="processing-view">
              <div className="spinner"></div>
              <p>Analizando imagen...</p>
              <p className="processing-text">Buscando prendas en la imagen</p>
            </div>
          )}

          {!isActive && products.length === 0 && (
            <div className="idle-message">
              <p>Abre la cámara para comenzar a detectar prendas</p>
            </div>
          )}
        </div>
      </main>

      <footer className="client-footer">
        <p>FashionVision AI - Sistema de Detección de Prendas</p>
      </footer>

      {!showKioskCountdown && (
        <CountdownOverlay
          countdown={countdown}
          message={countdownMessage}
          onCancel={cancelAutoDetection}
        />
      )}

      {showKioskCountdown && kioskCountdown !== null && (
        <div className="countdown-overlay">
          <div className="countdown-modal">
            <h2 className="countdown-title">Tu sesión está por terminar</h2>
            <p className="countdown-subtitle">¿Deseas continuar?</p>
            <div className="countdown-number">{kioskCountdown}</div>
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