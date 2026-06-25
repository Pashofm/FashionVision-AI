/**
 * Hook de acceso a la cámara del dispositivo.
 *
 * @module hooks/useCamera
 * @description Maneja el ciclo de vida del stream de la cámara:
 *   - Apertura y cierre del stream MediaDevices
 *   - Captura de frames individuales como PNG data URL
 *   - Limpieza automática al desmontar el componente
 *
 * @returns {Object} Referencias y funciones de control de cámara
 */

import { useState, useRef, useEffect, useCallback } from 'react';

const useCamera = () => {
  const [stream, setStream] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState('');
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    streamRef.current = stream;
  }, [stream]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  /**
   * Abre la cámara trasera (environment) del dispositivo.
   */
  const openCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      
      setStream(mediaStream);
      setIsActive(true);
      setError('');
      
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      }, 100);
    } catch (err) {
      console.error('Error camera:', err);
      setError('No se pudo acceder a la cámara');
    }
  }, []);

  /**
   * Detiene el stream de la cámara y libera recursos.
   */
  const closeCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setIsActive(false);
  }, [stream]);

  /**
   * Captura un frame del video como imagen PNG.
   * @param {HTMLCanvasElement} canvas — Canvas para dibujar el frame
   * @returns {string|null} Data URL de la imagen en formato PNG
   */
  const captureFrame = useCallback((canvas) => {
    const video = videoRef.current;
    
    if (!video || !canvas) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    return canvas.toDataURL('image/png');
  }, []);

  return {
    videoRef,
    stream,
    isActive,
    error,
    openCamera,
    closeCamera,
    captureFrame
  };
};

export default useCamera;
