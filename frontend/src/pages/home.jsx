import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useCamera from '../hooks/useCamera';
import ButtonGroup from '../components/ButtonGroup';
import CameraSection from '../components/CameraSection';
import { detectClothes } from '../services/api';
import '../styles/home.css';

const PRODUCTOS_DB = {
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

const getProduct = (cls, conf) => {
  const producto = PRODUCTOS_DB[cls.toLowerCase()];
  if (producto) {
    return { ...producto, confidence: conf };
  }
  return { 
    name: cls, 
    price: 0, 
    brand: 'Desconocido', 
    sku: 'N/A', 
    confidence: conf, 
    tipoPrenda: cls,
    sizes: [],
    colors: []
  };
};

const traducirCategoria = (className) => {
  if (!className) return 'Prenda';
  const producto = PRODUCTOS_DB[className.toLowerCase()];
  return producto ? producto.tipoPrenda : className;
};

const detectarColor = (canvas) => {
  const ctx = canvas.getContext('2d');
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;

  let r = 0, g = 0, b = 0;
  let total = data.length / 4;

  for (let i = 0; i < data.length; i += 4) {
    r += data[i];
    g += data[i + 1];
    b += data[i + 2];
  }

  r = Math.floor(r / total);
  g = Math.floor(g / total);
  b = Math.floor(b / total);

  if (r > g && r > b) return 'Rojo';
  if (g > r && g > b) return 'Verde';
  if (b > r && b > g) return 'Azul';
  if (r > 200 && g > 200 && b > 200) return 'Blanco';
  if (r < 50 && g < 50 && b < 50) return 'Negro';

  return 'Color mixto';
};

const Home = () => {
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imagen, setImagen] = useState(null);
  const [colorDetectado, setColorDetectado] = useState('');
  const [detections, setDetections] = useState(null);
  const [imageSize, setImageSize] = useState(null);
  const [appError, setAppError] = useState('');
  const [isModelReady, setIsModelReady] = useState(true);
  const navigate = useNavigate();

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
    setAppError('');
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

      const color = detectarColor(canvas);
      setColorDetectado(color);

      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        
        try {
          const result = await detectClothes(file);
          
          if (result.detections && result.detections.length > 0) {
            const detection = result.detections[0];
            setDetections(result.detections);
            setImageSize(result.image_size);
            setProducto(getProduct(detection.class, detection.confidence));
          } else {
            setAppError('No se detectó una prenda de vestir. Intenta con otra imagen.');
          }
        } catch (err) {
          console.error('Error en detección:', err);
          setAppError('Error al procesar la imagen en el servidor');
        } finally {
          setLoading(false);
        }
      }, 'image/jpeg');

    } catch (err) {
      console.error('Error procesando imagen:', err);
      setAppError('Error al procesar la imagen');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (imagen && detections && detections.length > 0 && resultCanvasRef.current) {
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
          ctx.lineWidth = 3;
          ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);
          
          ctx.fillStyle = '#00ff00';
          ctx.font = 'bold 16px sans-serif';
          ctx.fillText(
            `${traducirCategoria(det.class)} ${Math.round(det.confidence * 100)}%`,
            sx1,
            sy1 - 8
          );
        });
      };
      
      imgEl.src = imagen;
    }
  }, [imagen, detections, imageSize]);

  const handleCapture = useCallback(() => {
    const canvas = canvasRef.current;
    const capturedImage = captureFrame(canvas);
    
    if (capturedImage) {
      closeCamera();
      processDetection(capturedImage);
    }
  }, [captureFrame, closeCamera, processDetection]);

  const handleDemoBackend = async () => {
    setLoading(true);
    setAppError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      const result = await response.json();
      if (result.status === 'healthy') {
        setIsModelReady(true);
        setAppError('Backend YOLO conectado correctamente');
      }
    } catch (err) {
      console.error('Error conectando con el backend:', err);
      setAppError('Error conectando con el backend YOLO');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setProducto(null);
    setImagen(null);
    setColorDetectado('');
    setDetections(null);
  };

  const error = cameraError || appError;

  return (
    <div className="home-page">
      <header>
        <div className="logo">FashionVision IA</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/pago')}>Pago</button>
          <button>Inventario</button>
        </nav>
      </header>

      <main className="container">
        {error && <div className="error-message">{error}</div>}

        <section className="button-section">
          <ButtonGroup 
            onOpenCamera={openCamera}
            onDemoBackend={handleDemoBackend}
            isModelReady={isModelReady}
            isLoading={loading}
          />
        </section>

        <canvas ref={canvasRef} style={{ display: 'none' }} />

        <CameraSection 
          videoRef={videoRef}
          isActive={isActive}
          onCapture={handleCapture}
          onClose={closeCamera}
          isModelReady={isModelReady}
        />

        {loading ? (
          <section className="preview-section">
            <div className="preview-loading">
              <div className="spinner"></div>
              <p>Analizando imagen...</p>
            </div>
          </section>
        ) : imagen ? (
          <section className="preview-section detection-result">
            <div className="image-container">
              {detections && detections.length > 0 ? (
                <canvas ref={resultCanvasRef} className="preview-image" />
              ) : (
                <img src={imagen} alt="Capturada" className="preview-image" />
              )}
            </div>
            
            {producto ? (
              <div className="product-info">
                <div className="product-type-badge">{producto.tipoPrenda}</div>
                <h2 className="product-name">{producto.name}</h2>
                <p className="product-brand-sku">{producto.brand} - {producto.sku}</p>
                
                <div className="price-display">
                  <span>Precio</span>
                  <span className="price">${producto.price.toFixed(2)}</span>
                </div>

                <div className="details-grid">
                  <div className="detail-item">
                    <span className="detail-label">Marca</span>
                    <span className="detail-value">{producto.brand}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">SKU</span>
                    <span className="detail-value">{producto.sku}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Color detectado</span>
                    <span className="detail-value">{colorDetectado}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Confianza</span>
                    <span className="detail-value confidence">{(producto.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {producto.sizes && producto.sizes.length > 0 && (
                  <div className="tags-section">
                    <span className="tags-label">Tallas disponibles</span>
                    <div className="tags-list">
                      {producto.sizes.map(s => <span key={s} className="tag">{s}</span>)}
                    </div>
                  </div>
                )}

                {producto.colors && producto.colors.length > 0 && (
                  <div className="tags-section">
                    <span className="tags-label">Colores disponibles</span>
                    <div className="tags-list">
                      {producto.colors.map(c => <span key={c} className="tag">{c}</span>)}
                    </div>
                  </div>
                )}

                <button className="btn-save" onClick={reset}>
                  Nueva Captura
                </button>
              </div>
            ) : (
              <div className="no-detection">
                <h3>No se detectó prenda</h3>
                <p>Intenta con mejor iluminación</p>
                <button className="btn-outline" onClick={reset}>
                  Intentar de nuevo
                </button>
              </div>
            )}
          </section>
        ) : null}
      </main>
    </div>
  );
};

export default Home;
