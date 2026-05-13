import { useState, useRef, useCallback, useEffect } from 'react';
import { detectClothes } from '../services/api';

const DETECTION_INTERVAL = 300;
const MIN_CONFIDENCE = 0.05;

const useRealTimeDetection = () => {
  const [isDetecting, setIsDetecting] = useState(false);
  const [lastDetections, setLastDetections] = useState([]);
  const [error, setError] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const isActiveRef = useRef(false);

  const captureFrame = useCallback((canvas) => {
    const video = videoRef.current;
    if (!video || !canvas) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    return canvas.toDataURL('image/jpeg', 0.8);
  }, []);

  const performDetection = useCallback(async () => {
    if (!isActiveRef.current || !videoRef.current) return;

    try {
      const canvas = canvasRef.current;
      const imgData = captureFrame(canvas);

      if (!imgData) return;

      const imgElement = new Image();
      imgElement.src = imgData;

      await new Promise((resolve) => {
        imgElement.onload = resolve;
      });

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = imgElement.width;
      tempCanvas.height = imgElement.height;
      const ctx = tempCanvas.getContext('2d');
      ctx.drawImage(imgElement, 0, 0);

      tempCanvas.toBlob(async (blob) => {
        if (!blob) return;

        const file = new File([blob], 'frame.jpg', { type: 'image/jpeg' });

        try {
          const result = await detectClothes(file);

          if (result.detections && result.detections.length > 0) {
            const filteredDetections = result.detections.filter(
              d => d.confidence >= MIN_CONFIDENCE
            );

            if (filteredDetections.length > 0) {
              setLastDetections(filteredDetections.map(d => ({
                class: d.class,
                confidence: d.confidence,
                bbox: d.bbox,
                imageSize: result.image_size || [imgElement.width, imgElement.height]
              })));
              setError(null);
            }
          } else {
            setLastDetections([]);
          }
        } catch (err) {
          console.error('Detection error:', err);
          setError('Error en detección');
        }
      }, 'image/jpeg', 0.8);
    } catch (err) {
      console.error('Frame capture error:', err);
    }
  }, [captureFrame]);

  const startDetection = useCallback((videoElementRef) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    videoRef.current = videoElementRef.current;
    isActiveRef.current = true;
    setIsDetecting(true);
    setError(null);
    setLastDetections([]);

    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }

    performDetection();

    intervalRef.current = setInterval(performDetection, DETECTION_INTERVAL);
  }, [performDetection]);

  const pauseDetection = useCallback(() => {
    isActiveRef.current = false;
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const stopDetection = useCallback(() => {
    isActiveRef.current = false;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setIsDetecting(false);
    setLastDetections([]);
    setError(null);
  }, []);

  const resumeDetection = useCallback(() => {
    if (!isActiveRef.current && videoRef.current) {
      isActiveRef.current = true;
      setIsDetecting(true);
      performDetection();
      intervalRef.current = setInterval(performDetection, DETECTION_INTERVAL);
    }
  }, [performDetection]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isDetecting,
    lastDetections,
    error,
    startDetection,
    stopDetection,
    pauseDetection,
    resumeDetection,
    videoRef
  };
};

export default useRealTimeDetection;