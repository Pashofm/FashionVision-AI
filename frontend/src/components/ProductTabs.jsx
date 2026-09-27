import React from 'react';
import '../styles/product-tabs.css';

const ProductTabs = ({ products, activeTabIndex, onSelectTab, onRemoveTab }) => {
  if (!products || products.length === 0) return null;

  return (
    <div className="product-tabs-container">
      <div className="product-tabs">
        {products.map((product, index) => (
          <div
            key={product.id}
            className={`product-tab ${activeTabIndex === index ? 'active' : ''}`}
            onClick={() => onSelectTab(index)}
          >
            <span className="tab-icon">
              {product.tipoProducto?.charAt(0) || 'P'}
            </span>
            <span className="tab-name">
              {product.name?.length > 12 ? `${product.name.substring(0, 12)}...` : product.name}
            </span>
            {product.matchingVariant && product.matchingVariant.quantity_available > 0 && (
              <span className="tab-check">✓</span>
            )}
            <button
              className="product-tab-close"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveTab(product.id);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
      {products.length >= 5 && (
        <div className="products-limit-warning">
          Máximo 5 productos
        </div>
      )}
    </div>
  );
};

export default ProductTabs;