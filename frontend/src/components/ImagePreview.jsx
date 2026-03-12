import React from 'react';

const ImagePreview = ({ 
  image, 
  color, 
  tipoPrenda, 
  confianza, 
  onSave 
}) => {
  if (!image) return null;

  return (
    <section className="preview-section">
      <img src={image} alt="Capturada" className="preview-image" />
      <div className="preview-info">
        <div className="preview-item">
          <span className="preview-label">Color detectado:</span>
          <span className="preview-value">{color}</span>
        </div>
        <div className="preview-item">
          <span className="preview-label">Tipo detectado:</span>
          <span className="preview-value">{tipoPrenda}</span>
        </div>
        {confianza !== undefined && (
          <div className="preview-item">
            <span className="preview-label">Confianza:</span>
            <span className="preview-value confidence">
              {(confianza * 100).toFixed(0)}%
            </span>
          </div>
        )}
        <button className="btn-save" onClick={onSave}>
          ✓ Guardar al Inventario
        </button>
      </div>
    </section>
  );
};

export default ImagePreview;
