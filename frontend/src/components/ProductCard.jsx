import React from 'react';

const ProductCard = ({ producto }) => {
  if (!producto) return null;

  return (
    <div className="product-card">
      <h3>✨ Análisis de Prenda</h3>
      <hr style={{ border: '0.5px solid #eee', marginBottom: '15px' }} />
      <p><strong>Categoría:</strong> {producto.prenda}</p>
      <p><strong>Color predominante:</strong> {producto.color}</p>
      <p><strong>Confianza:</strong> {(producto.confianza * 100).toFixed(0)}%</p>
    </div>
  );
};

export default ProductCard;
