/**
 * Hook de Auto-Detección para el módulo Kiosko.
 *
 * @module hooks/useAutoDetection
 * @description Maneja el ciclo de vida de la detección automática de prendas:
 *   1. `detecting` — Buscando prenda frente a la cámara (timeout 10s)
 *   2. `countdown` — Prenda detectada, cuenta regresiva de 3s
 *   3. `capturing` — Dispara captura y procesamiento
 *   4. `paused` / `idle` — Estados de pausa y reposo
 *
 * @param {Function} onCaptureTriggered — Callback ejecutado al finalizar la cuenta regresiva
 * @returns {Object} Estado y funciones de control
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const COUNTDOWN_SECONDS = 3;
const DETECTION_TIMEOUT = 10000;

const useAutoDetection = (onCaptureTriggered) => {
  const [status, setStatus] = useState('idle');
  const [countdown, setCountdown] = useState(null);
  const [message, setMessage] = useState('');

  const countdownIntervalRef = useRef(null);
  const timeoutRef = useRef(null);
  const captureCallbackRef = useRef(onCaptureTriggered);
  const statusRef = useRef(status);

  useEffect(() => {
    captureCallbackRef.current = onCaptureTriggered;
  }, [onCaptureTriggered]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const clearTimers = useCallback(() => {
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const startCountdown = useCallback(() => {
    clearTimers();
    setStatus('countdown');
    setCountdown(COUNTDOWN_SECONDS);
    setMessage('Prenda detectada, no te muevas por favor');

    let currentCount = COUNTDOWN_SECONDS;

    countdownIntervalRef.current = setInterval(() => {
      currentCount -= 1;
      setCountdown(currentCount);

      if (currentCount <= 0) {
        clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = null;
        setStatus('capturing');

        if (captureCallbackRef.current) {
          captureCallbackRef.current();
        }
      }
    }, 1000);
  }, [clearTimers]);

  const cancelAutoDetection = useCallback(() => {
    clearTimers();
    setStatus('idle');
    setCountdown(null);
    setMessage('');
  }, [clearTimers]);

  const startAutoDetection = useCallback(() => {
    clearTimers();
    setStatus('detecting');
    setMessage('Detectando prenda...');

    timeoutRef.current = setTimeout(() => {
      if (status === 'detecting') {
        setMessage('Acerca la prenda a la cámara');
      }
    }, DETECTION_TIMEOUT);
  }, [clearTimers, status]);

  const pauseDetection = useCallback(() => {
    clearTimers();
    setStatus('paused');
    setCountdown(null);
    setMessage('');
  }, [clearTimers]);

  const resetFromPause = useCallback(() => {
    clearTimers();
    setStatus('idle');
    setCountdown(null);
    setMessage('');
  }, [clearTimers]);

  const onFirstDetection = useCallback(() => {
    if (statusRef.current === 'detecting') {
      clearTimers();
      startCountdown();
    }
  }, [clearTimers, startCountdown]);

  const onProcessingComplete = useCallback(() => {
    setStatus('idle');
    setCountdown(null);
    setMessage('');
  }, []);

  useEffect(() => {
    return () => {
      clearTimers();
    };
  }, [clearTimers]);

  return {
    status,
    countdown,
    message,
    startAutoDetection,
    cancelAutoDetection,
    pauseDetection,
    resetFromPause,
    onFirstDetection,
    onProcessingComplete
  };
};

export default useAutoDetection;
