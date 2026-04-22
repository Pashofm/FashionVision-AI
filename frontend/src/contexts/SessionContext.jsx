import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionTimeout } from '../hooks/useSessionTimeout';
import { isAuthenticated, getStoredUser, refreshToken } from '../services/api';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [showExpiredModal, setShowExpiredModal] = useState(false);
  const [savedState, setSavedState] = useState(null);
  const navigate = useNavigate();

  const user = getStoredUser();

  const handleSessionExpiring = useCallback(() => {
    console.log('Session expiring soon...');
  }, []);

  const handleSessionExpired = useCallback(async () => {
    setShowExpiredModal(true);
  }, []);

  useSessionTimeout(handleSessionExpiring, handleSessionExpired);

  const handleSilentReLogin = useCallback(async () => {
    try {
      await refreshToken();
      setShowExpiredModal(false);
    } catch (error) {
      setShowExpiredModal(false);
      navigate('/');
    }
  }, [navigate]);

  const saveCurrentState = useCallback(() => {
    const currentPath = window.location.pathname;
    setSavedState({ path: currentPath });
  }, []);

  const clearSavedState = useCallback(() => {
    setSavedState(null);
  }, []);

  return (
    <SessionContext.Provider value={{ savedState, saveCurrentState, clearSavedState }}>
      {children}
      {showExpiredModal && (
        <div className="session-expired-overlay">
          <div className="session-expired-modal">
            <h2>Sesión expirada</h2>
            <p>Tu sesión ha expirado por inactividad.</p>
            <button onClick={handleSilentReLogin} className="relogin-btn">
              Reanudar sesión
            </button>
          </div>
        </div>
      )}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return context;
}
