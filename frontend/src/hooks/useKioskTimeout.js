/**
 * Hook de timeout de inactividad para el módulo Kiosko.
 *
 * @module hooks/useKioskTimeout
 * @description Detecta inactividad del usuario y ejecuta un cierre de sesión
 *   automático después de 2 minutos sin interacción, con una cuenta regresiva
 *   de 10 segundos para que el usuario pueda cancelar.
 *
 * @param {Function} onSessionEnd — Callback ejecutado al expirar la sesión
 * @param {boolean} [enabled=true] — Deshabilita el timer si es false
 * @returns {{ countdown: number|null, resetTimer: Function }}
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { isAuthenticated, extendSession } from '../services/api';

const KIOSK_TIMEOUT_MS = 2 * 60 * 1000;
const COUNTDOWN_SECONDS = 10;

export function useKioskTimeout(onSessionEnd, enabled = true) {
  const timeoutRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  const sessionEndingRef = useRef(false);
  const [countdown, setCountdown] = useState(null);

  const clearAllTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
  }, []);

  const startCountdown = useCallback(() => {
    setCountdown(COUNTDOWN_SECONDS);
    countdownIntervalRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearAllTimers();
          sessionEndingRef.current = true;
          setCountdown(null);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [clearAllTimers]);

  const startKioskTimer = useCallback(() => {
    clearAllTimers();
    timeoutRef.current = setTimeout(() => {
      startCountdown();
    }, KIOSK_TIMEOUT_MS);
  }, [clearAllTimers, startCountdown]);

  /**
   * Reinicia el timer de inactividad y extiende la sesión en el servidor.
   */
  const resetTimer = useCallback(async () => {
    if (countdown !== null) {
      clearAllTimers();
      setCountdown(null);
    }
    sessionEndingRef.current = false;
    try {
      await extendSession();
    } catch (err) {
      console.warn('Failed to extend session on server:', err);
    }
    startKioskTimer();
  }, [countdown, clearAllTimers, startKioskTimer]);

  useEffect(() => {
    if (sessionEndingRef.current && countdown === null) {
      sessionEndingRef.current = false;
      if (onSessionEnd) {
        onSessionEnd();
      }
    }
  }, [countdown, onSessionEnd]);

  useEffect(() => {
    if (!isAuthenticated() || !enabled) {
      return;
    }
    startKioskTimer();
    return () => {
      clearAllTimers();
    };
  }, [startKioskTimer, clearAllTimers, enabled]);

  return { countdown, resetTimer };
}
