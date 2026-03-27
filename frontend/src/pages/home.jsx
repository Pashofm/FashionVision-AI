import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useTensorFlow from '../hooks/useTensorFlow';
import useCamera from '../hooks/useCamera';
import { traducirCategoria, detectarColor } from '../utils/imageProcessing';
import ButtonGroup from '../components/ButtonGroup';
import CameraSection from '../components/CameraSection';
import ImagePreview from '../components/ImagePreview';
import ProductCard from '../components/ProductCard';
import InventoryTable from '../components/InventoryTable';
import '../styles/home.css';

const Home = () => {
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imagen, setImagen] = useState(null);
  const [color, setColor] = useState('');
  const [tipoPrenda, setTipoPrenda] = useState('');
  const [productos, setProductos] = useState([]);
  const [appError, setAppError] = useState('');
  const navigate = useNavigate();
  const { model, isReady, error: modelError } = useTensorFlow();
  const { 
    videoRef, 
    isActive, 
    error: cameraError, 
    openCamera, 
    closeCamera, 
    captureFrame 
  } = useCamera();

  const canvasRef = useRef(null);

  const processImage = useCallback(async (imgData) => {
    setImagen(imgData);
    setAppError('');

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

    const colorDetectado = detectarColor(canvas);
    setColor(colorDetectado);

    if (!model) {
      console.log('Modelo aún no cargado');
      return;
    }

    try {
      await imgElement.decode();
      const predictions = await model.classify(imgElement);
      console.log('Predicciones:', predictions);

      if (predictions.length > 0) {
        let categoriaTraducida = null;
        let predictionIndex = 0;

        for (let i = 0; i < predictions.length; i++) {
          const categoria = traducirCategoria(predictions[i].className);
          if (categoria !== null) {
            categoriaTraducida = categoria;
            predictionIndex = i;
            break;
          }
        }

        if (categoriaTraducida) {
          setTipoPrenda(categoriaTraducida);
          setProducto({
            prenda: categoriaTraducida,
            color: colorDetectado,
            confianza: predictions[predictionIndex].probability
          });
        } else {
          setAppError('No se detectó una prenda de vestir. Intenta con otra imagen.');
        }
      }
    } catch (err) {
      console.error('Error clasificando:', err);
      setAppError('Error al procesar la imagen');
    }
  }, [model]);

  const handleCapture = useCallback(() => {
    const canvas = canvasRef.current;
    const capturedImage = captureFrame(canvas);
    
    if (capturedImage) {
      closeCamera();
      processImage(capturedImage);
    }
  }, [captureFrame, closeCamera, processImage]);

  const handleDemoBackend = async () => {
    setLoading(true);
    setAppError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/test-detection');
      const result = await response.json();
      setProducto(result.data);
    } catch (err) {
      console.error('Error conectando con el backend:', err);
      setAppError('Error conectando con el backend');
    } finally {
      setLoading(false);
    }
  };

  const saveProduct = () => {
    if (!producto) return;

    const nuevoProducto = {
      id: Date.now(),
      nombre: tipoPrenda || 'Producto',
      cantidad: 1,
      precio: 0,
      color,
      tipoPrenda,
      imagen
    };

    setProductos([...productos, nuevoProducto]);
    setProducto(null);
    setImagen(null);
    setColor('');
    setTipoPrenda('');
  };

  const error = modelError || cameraError || appError;

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
            isModelReady={isReady}
            isLoading={loading}
          />
        </section>

        <canvas ref={canvasRef} style={{ display: 'none' }} />

        <CameraSection 
          videoRef={videoRef}
          isActive={isActive}
          onCapture={handleCapture}
          onClose={closeCamera}
          isModelReady={isReady}
        />

        <ImagePreview 
          image={imagen}
          color={color}
          tipoPrenda={tipoPrenda}
          confianza={producto?.confianza}
          onSave={saveProduct}
        />

        <section className="inventory">
          {!producto && productos.length === 0 ? (
            <p>No se encuentran productos en el inventario</p>
          ) : (
            <>
              <ProductCard producto={producto} />
              <InventoryTable productos={productos} />
            </>
          )}
        </section>
      </main>
    </div>
  );
};

export default Home;
