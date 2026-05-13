import React from 'react';
import '../styles/product-tab-panel.css';

const ProductTabPanel = ({
  product,
  onSizeSelect,
  onColorSelect,
  onAddToCart,
  onRemove
}) => {
  if (!product) return null;

  const canAdd = product.selectedSize &&
                 product.selectedColor &&
                 product.matchingVariant &&
                 product.matchingVariant.quantity_available > 0;

  return (
    <div className="product-tab-panel">
      <div className="panel-header">
        <span className="product-badge">{product.tipoProducto}</span>
        <button className="panel-remove-btn" onClick={() => onRemove(product.id)}>
          Eliminar
        </button>
      </div>

      <h2 className="product-name">{product.name}</h2>
      <p className="product-brand">{product.marca}</p>

      <div className="price-tag">
        <span className="price">${product.precio?.toFixed(2) || '0.00'}</span>
      </div>

      <div className="product-details">
        <div className="detail-row">
          <span className="detail-label">SKU</span>
          <span className="detail-value">{product.sku}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Confianza</span>
          <span className="detail-value confidence">
            {((product.confidence || 0) * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {product.sizes && product.sizes.length > 0 && (
        <div className="tags-section">
          <span className="tags-label">Tallas</span>
          <div className="tags-list">
            {product.sizes.map((s, idx) => (
              <button
                key={`size-${idx}`}
                className={`tag ${product.selectedSize?.id === s.id || product.selectedSize?.name === s.name ? 'selected' : ''} ${s.stock === 0 ? 'out-of-stock' : ''}`}
                onClick={() => s.stock > 0 && onSizeSelect(product.id, s)}
                disabled={s.stock === 0}
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {product.colors && product.colors.length > 0 && (
        <div className="tags-section">
          <span className="tags-label">Colores</span>
          <div className="tags-list">
            {product.colors.map((c, idx) => (
              <button
                key={`color-${idx}`}
                className={`tag ${product.selectedColor?.id === c.id || product.selectedColor?.name === c.name ? 'selected' : ''} ${c.stock === 0 ? 'out-of-stock' : ''}`}
                onClick={() => c.stock > 0 && onColorSelect(product.id, c)}
                disabled={c.stock === 0}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {product.selectionError && (
        <div className="selection-error">
          {product.selectionError}
        </div>
      )}

      <div className="action-buttons">
        <button
          className="btn-add-cart"
          onClick={() => onAddToCart(product.id)}
          disabled={!canAdd}
        >
          🛒 Agregar al Carrito
        </button>
      </div>
    </div>
  );
};

export default ProductTabPanel;