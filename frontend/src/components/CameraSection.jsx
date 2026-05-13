import React from 'react';

const CameraSection = ({
  onClose,
  showCloseButton = true
}) => {
  if (!showCloseButton) return null;

  return (
    <section className="camera-section">
      <div className="camera-controls">
        <button className="btn-cancel" onClick={onClose}>
          ✕ Cerrar
        </button>
      </div>
    </section>
  );
};

export default CameraSection;