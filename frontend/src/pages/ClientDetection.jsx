import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/client-detection.css';

const DATASET_PRODUCTS = {
  'gorra-roja-lacoste': {
    name: 'Gorra Roja Lacoste',
    price: 999.99,
    brand: 'Lacoste',
    sku: 'GOR-001',
    sizes: ['One Size'],
    colors: ['Rojo'],
    tipoPrenda: 'Gorra'
  },
  'top': {
    name: 'Camiseta Algodon',
    price: 299.99,
    brand: 'FashionCo',
    sku: 'CAM-001',
    sizes: ['S', 'M', 'L', 'XL'],
    colors: ['Blanco', 'Negro'],
    tipoPrenda: 'Camiseta'
  },
  'pants': {
    name: 'Jean Slim Fit',
    price: 599.99,
    brand: 'DenimCraft',
    sku: 'PAN-001',
    sizes: ['28', '30', '32', '34'],
    colors: ['Azul', 'Negro'],
    tipoPrenda: 'Pantalón'
  }
};

const getProductFromClass = (className, confidence) => {
  const producto = DATASET_PRODUCTS[className.toLowerCase()];
  if (producto) {
    return { ...producto, confidence };
  }
  return {
    name: className,
    price: 0,
    brand: 'Desconocido',
    sku: 'N/A',
    confidence,
    tipoPrenda: className,
    sizes: [],
    colors: []
  };
};

const ClientDetection = () => {
  const [view, setView] = useState('idle');
  const [imagen, setImagen] = useState(null);
  const [producto, setProducto] = useState(null);
  const [detections, setDetections] = useState(null);
  const [imageSize, setImageSize] = useState(null);
  const [, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [carrito, setCarrito] = useState([]);
  const [mostrarCarrito, setMostrarCarrito] = useState(false);
  const navigate = useNavigate();

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const resultCanvasRef = useRef(null);
  const mediaStreamRef = useRef(null);

  const initCamera = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setView('camera');
    } catch (err) {
      console.error('Camera error:', err);
      setError('No se pudo acceder a la cámara. Verifica los permisos.');
    }
  };

  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setView('idle');
  };

  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || video.readyState !== 4) {
      setError('Video no está listo');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      const imgUrl = URL.createObjectURL(blob);
      setImagen(imgUrl);
      simulateDetection(imgUrl);
    }, 'image/jpeg');
  };

  const simulateDetection = (imgUrl) => {
    setView('processing');
    setLoading(true);
    setError('');

    setTimeout(() => {
      const classes = Object.keys(DATASET_PRODUCTS);
      const randomClass = classes[Math.floor(Math.random() * classes.length)];
      const confidence = 0.85 + Math.random() * 0.14;

      const imgElement = new Image();
      imgElement.onload = () => {
        const imgW = imgElement.width;
        const imgH = imgElement.height;
        const x1 = imgW * 0.2 + Math.random() * imgW * 0.3;
        const y1 = imgH * 0.2 + Math.random() * imgH * 0.3;
        const x2 = x1 + imgW * 0.3;
        const y2 = y1 + imgH * 0.35;

        const fakeDetections = [{
          class: randomClass,
          confidence: confidence,
          bbox: [x1, y1, x2, y2]
        }];

        setDetections(fakeDetections);
        setImageSize([imgW, imgH]);
        setProducto(getProductFromClass(randomClass, confidence));
        setView('result');
        setLoading(false);
      };
      imgElement.src = imgUrl;
    }, 1500);
  };

  const drawBoundingBoxes = useCallback(() => {
    if (view !== 'result' || !imagen || !detections || detections.length === 0 || !resultCanvasRef.current) {
      return;
    }

    const canvas = resultCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const imgEl = new Image();

    imgEl.onload = () => {
      canvas.width = imgEl.width;
      canvas.height = imgEl.height;
      ctx.drawImage(imgEl, 0, 0);

      const [imgW, imgH] = imageSize || [imgEl.width, imgEl.height];

      detections.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const scaleX = imgEl.width / imgW;
        const scaleY = imgEl.height / imgH;

        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const sx2 = x2 * scaleX;
        const sy2 = y2 * scaleY;

        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 4;
        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

        ctx.fillStyle = '#00ff00';
        ctx.font = 'bold 18px sans-serif';
        const label = `${det.class.toUpperCase()} ${Math.round(det.confidence * 100)}%`;
        const textMetrics = ctx.measureText(label);
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(sx1, sy1 - 28, textMetrics.width + 16, 28);
        ctx.fillStyle = '#00ff00';
        ctx.fillText(label, sx1 + 8, sy1 - 8);
      });
    };
    imgEl.src = imagen;
  }, [view, imagen, detections, imageSize]);

  React.useEffect(() => {
    drawBoundingBoxes();
  }, [drawBoundingBoxes]);

  const agregarAlCarrito = () => {
    if (producto) {
      setCarrito(prev => [...prev, { ...producto, id: Date.now() }]);
      setProducto(null);
      setImagen(null);
      setDetections(null);
      setView('idle');
    }
  };

  const eliminarDelCarrito = (id) => {
    setCarrito(prev => prev.filter(item => item.id !== id));
  };

  const totalesCarrito = () => {
    const total = carrito.reduce((sum, item) => sum + item.price, 0);
    return { items: carrito.length, total };
  };

  const reset = () => {
    setProducto(null);
    setImagen(null);
    setDetections(null);
    setView('idle');
    setError('');
  };

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
          <button
            className="btn-admin"
            onClick={() => navigate('/dashboard')}
          >
            Panel Admin
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
                <div key={item.id} className="carrito-item">
                  <div className="item-info">
                    <span className="item-name">{item.name}</span>
                    <span className="item-price">${item.price.toFixed(2)}</span>
                  </div>
                  <button
                    className="btn-eliminar"
                    onClick={() => eliminarDelCarrito(item.id)}
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
              <button className="btn-enviar">
                Enviar al Admin para Pago
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

          {error && <div className="error-message">{error}</div>}

          {view === 'idle' && (
            <div className="idle-view">
              <div className="idle-icon">📷</div>
              <p className="idle-text">
                Presiona el botón para abrir la cámara y detectar prendas
              </p>
              <button className="btn-primary" onClick={initCamera}>
                <span>📷</span> Abrir Cámara
              </button>
            </div>
          )}

          {view === 'camera' && (
            <div className="camera-view">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="camera-video"
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
              <div className="camera-controls">
                <button className="btn-capture" onClick={capture}>
                  <span>⏺</span> Capturar
                </button>
                <button className="btn-cancel" onClick={stopCamera}>
                  ✕ Cerrar
                </button>
              </div>
            </div>
          )}

          {view === 'processing' && (
            <div className="processing-view">
              <div className="spinner"></div>
              <p>Analizando imagen...</p>
              <p className="processing-text">Buscando prendas en la imagen</p>
            </div>
          )}

          {view === 'result' && (
            <div className="result-view">
              <div className="result-image-container">
                {detections && detections.length > 0 ? (
                  <canvas ref={resultCanvasRef} className="result-canvas" />
                ) : (
                  <img src={imagen} alt="Capturada" className="result-image" />
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
    </div>
  );
};

export default ClientDetection;
