import React from 'react';

const ButtonGroup = ({ 
  onOpenCamera, 
  onDemoBackend, 
  isModelReady, 
  isLoading 
}) => {
  return (
    <div className="button-group">
      <button 
        className="btn-primary" 
        onClick={onOpenCamera} 
        disabled={!isModelReady}
      >
        <span className="btn-icon">📷</span>
        <span className="btn-text">
          {isModelReady ? 'Abrir Cámara' : 'Cargando IA...'}
        </span>
      </button>
      
      <button 
        className="btn-outline" 
        onClick={onDemoBackend} 
        disabled={isLoading}
      >
        <span className="btn-icon">⚡</span>
        <span className="btn-text">
          {isLoading ? 'Procesando...' : 'Demo Backend'}
        </span>
      </button>
    </div>
  );
};

export default ButtonGroup;
