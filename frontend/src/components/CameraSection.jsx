import React from 'react';

const CameraSection = ({ 
  videoRef, 
  isActive, 
  onCapture, 
  onClose, 
  isModelReady 
}) => {
  if (!isActive) return null;

  return (
    <section className="camera-section">
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline 
        muted
        className="camera-video" 
      />
      <div className="camera-buttons">
        <button 
          className="btn-capture" 
          onClick={onCapture} 
          disabled={!isModelReady}
        >
          <span>⏺</span> Capturar
        </button>
        <button className="btn-cancel" onClick={onClose}>
          ✕ Cerrar
        </button>
      </div>
    </section>
  );
};

export default CameraSection;
