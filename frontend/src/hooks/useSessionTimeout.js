import { useEffect, useRef, useCallback } from 'react';
import { extendSession, isAuthenticated } from '../services/api';

const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000;
const EXTEND_INTERVAL_MS = 5 * 60 * 1000;

export function useSessionTimeout(onSessionExpiring, onSessionExpired) {
  const timeoutRef = useRef(null);
  const extendIntervalRef = useRef(null);
  const lastActivityRef = useRef(null);

  const checkAndExtendSession = useCallback(async () => {
    if (lastActivityRef.current === null) return;
    const timeSinceActivity = Date.now() - lastActivityRef.current;
    if (timeSinceActivity >= INACTIVITY_TIMEOUT_MS) {
      try {
        await extendSession();
        lastActivityRef.current = Date.now();
        if (onSessionExpiring) {
          onSessionExpiring();
        }
      } catch {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        if (onSessionExpired) {
          onSessionExpired();
        }
      }
    }
  }, [onSessionExpiring, onSessionExpired]);

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      checkAndExtendSession();
    }, INACTIVITY_TIMEOUT_MS);
  }, [checkAndExtendSession]);

  useEffect(() => {
    if (!isAuthenticated()) {
      return;
    }

    lastActivityRef.current = Date.now();

    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

    const handleActivity = () => {
      resetTimer();
    };

    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    resetTimer();

    extendIntervalRef.current = setInterval(async () => {
      if (isAuthenticated()) {
        try {
          await extendSession();
        } catch {
          if (onSessionExpired) {
            onSessionExpired();
          }
        }
      }
    }, EXTEND_INTERVAL_MS);

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (extendIntervalRef.current) {
        clearInterval(extendIntervalRef.current);
      }
    };
  }, [resetTimer, onSessionExpired]);
}

export function getTimeUntilExpiration() {
  const expiresIn = localStorage.getItem('expires_in');
  if (!expiresIn) return 0;
  return parseInt(expiresIn, 10) * 1000 - Date.now();
}