import { useEffect, useRef, useCallback, useState } from 'react';
import { isAuthenticated, extendSession } from '../services/api';

const KIOSK_TIMEOUT_MS = 2 * 60 * 1000;
const COUNTDOWN_SECONDS = 10;

export function useKioskTimeout(onSessionEnd) {
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
    if (!isAuthenticated()) {
      return;
    }
    startKioskTimer();
    return () => {
      clearAllTimers();
    };
  }, [startKioskTimer, clearAllTimers]);

  return { countdown, resetTimer };
}