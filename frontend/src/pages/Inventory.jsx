import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHeaders, getCategories, getLowStockProducts, getInventoryMovements } from '../services/api';
import { formatLocalDateTime } from '../utils/dateUtils';
import './Inventory.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Inventory = () => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showProductModal, setShowProductModal] = useState(false);
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingVariant, setEditingVariant] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [movements, setMovements] = useState([]);
  const [error, setError] = useState('');

  const [productForm, setProductForm] = useState({
    name: '',
    sku: '',
    base_price: '',
    description: '',
    category_id: '',
    yolo_class_name: '',
    images: []
  });

  const [variantForm, setVariantForm] = useState({
    size: '',
    color: '',
    color_hex: '#000000',
    sku_variant: '',
    price_modifier: '0'
  });

  const [stockForm, setStockForm] = useState({
    quantity: '',
    reason: '',
    type: 'restock'
  });

  const isAdmin = userData?.role === 'admin';

  const loadProducts = useCallback(async () => {
    try {
      const headers = getHeaders();
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category_id', selectedCategory);

      const response = await fetch(`${API_URL}/api/products/stock/all?${params}`, { headers });
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (err) {
      console.error('Error loading products:', err);
    }
  }, [searchTerm, selectedCategory]);

  const loadLowStock = useCallback(async () => {
    try {
      const data = await getLowStockProducts();
      setLowStockItems(data);
    } catch (err) {
      console.error('Error loading low stock:', err);
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [cats, lowStock] = await Promise.all([
        getCategories(),
        getLowStockProducts()
      ]);
      setCategories(cats);
      setLowStockItems(lowStock);
      await loadProducts();
    } catch {
      setError('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  }, [loadProducts]);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setUserData(user);
    if (user.role !== 'admin') {
      navigate('/');
      return;
    }
    loadData();
  }, [navigate, loadData]);

  useEffect(() => {
    if (activeTab === 'products') {
      loadProducts();
    } else if (activeTab === 'lowstock') {
      loadLowStock();
    }
  }, [activeTab, loadProducts, loadLowStock]);

  const loadMovements = async (variantId) => {
    try {
      const data = await getInventoryMovements(variantId);
      setMovements(data);
    } catch (err) {
      console.error('Error loading movements:', err);
    }
  };

  const openProductModal = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({
        name: product.name,
        sku: product.sku,
        base_price: product.base_price,
        description: product.description || '',
        category_id: product.category_id,
        yolo_class_name: product.yolo_class_name || '',
        images: product.images || []
      });
    } else {
      setEditingProduct(null);
      setProductForm({
        name: '',
        sku: '',
        base_price: '',
        description: '',
        category_id: '',
        yolo_class_name: '',
        images: []
      });
    }
    setShowProductModal(true);
  };

  const closeProductModal = () => {
    setShowProductModal(false);
    setEditingProduct(null);
    setError('');
  };

  const openVariantModal = (product, variant = null) => {
    setSelectedProduct(product);
    if (variant) {
      setEditingVariant(variant);
      setVariantForm({
        size: variant.size || '',
        color: variant.color || '',
        color_hex: variant.color_hex || '#000000',
        sku_variant: variant.sku_variant,
        price_modifier: variant.price_modifier?.toString() || '0'
      });
    } else {
      setEditingVariant(null);
      setVariantForm({
        size: '',
        color: '',
        color_hex: '#000000',
        sku_variant: `${product.sku}-`,
        price_modifier: '0'
      });
    }
    setShowVariantModal(true);
  };

  const closeVariantModal = () => {
    setShowVariantModal(false);
    setEditingVariant(null);
    setSelectedProduct(null);
    setError('');
  };

  const openStockModal = async (product, variant) => {
    setSelectedProduct(product);
    setSelectedVariant(variant);
    setStockForm({ quantity: '', reason: '', type: 'restock' });
    await loadMovements(variant.id);
    setShowStockModal(true);
  };

  const closeStockModal = () => {
    setShowStockModal(false);
    setSelectedProduct(null);
    setSelectedVariant(null);
    setMovements([]);
    setError('');
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const headers = getHeaders();
      const method = editingProduct ? 'PUT' : 'POST';
      const url = editingProduct
        ? `${API_URL}/api/products/${editingProduct.id}`
        : `${API_URL}/api/products`;

      const payload = {
        ...productForm,
        base_price: parseFloat(productForm.base_price),
        yolo_class_id: productForm.yolo_class_name ? 1 : null
      };

      const response = await fetch(url, {
        method,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al guardar producto');
      }

      closeProductModal();
      loadProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleVariantSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const headers = getHeaders();
      const method = editingVariant ? 'PUT' : 'POST';
      const url = editingVariant
        ? `${API_URL}/api/products/${selectedProduct.id}/variants/${editingVariant.id}`
        : `${API_URL}/api/products/${selectedProduct.id}/variants`;

      const payload = {
        ...variantForm,
        price_modifier: parseFloat(variantForm.price_modifier) || 0,
        product_id: selectedProduct.id
      };

      const response = await fetch(url, {
        method,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al guardar variante');
      }

      closeVariantModal();
      loadProducts();
      if (selectedProduct?.id) {
        loadProductDetails(selectedProduct.id);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStockSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const headers = getHeaders();
      const payload = {
        quantity: parseInt(stockForm.quantity),
        reason: stockForm.reason
      };

      const endpoint = stockForm.type === 'restock'
        ? `${API_URL}/api/inventory/restock?variant_id=${selectedVariant.id}`
        : `${API_URL}/api/inventory/adjust?variant_id=${selectedVariant.id}`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al ajustar inventario');
      }

      setStockForm({ quantity: '', reason: '', type: 'restock' });
      loadMovements(selectedVariant.id);
      loadProducts();
      loadLowStock();
    } catch (err) {
      setError(err.message);
    }
  };

  const loadProductDetails = async (productId) => {
    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/products/${productId}/stock`, { headers });
      if (response.ok) {
        const data = await response.json();
        setSelectedProduct(data);
      }
    } catch (err) {
      console.error('Error loading product details:', err);
    }
  };

  const handleViewProduct = async (product) => {
    await loadProductDetails(product.id);
    setEditingProduct(product);
    setShowProductModal(true);
  };

  const handleImageUpload = async (productId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/products/${productId}/images`, {
        method: 'POST',
        headers,
        body: formData
      });

      if (response.ok) {
        await loadProductDetails(productId);
        await loadProducts();
      }
    } catch (err) {
      console.error('Error uploading image:', err);
    }
  };

  const handleImageDelete = async (productId, imageUrl) => {
    try {
      const headers = getHeaders();
      const encodedUrl = encodeURIComponent(imageUrl);
      const response = await fetch(`${API_URL}/api/products/${productId}/images?image_url=${encodedUrl}`, {
        method: 'DELETE',
        headers
      });

      if (response.ok) {
        await loadProductDetails(productId);
        await loadProducts();
      }
    } catch (err) {
      console.error('Error deleting image:', err);
    }
  };

  const deleteProduct = async (productId) => {
    if (!window.confirm('¿Estás seguro de eliminar este producto?')) return;

    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/products/${productId}`, {
        method: 'DELETE',
        headers
      });

      if (response.ok) {
        loadProducts();
      }
    } catch (err) {
      console.error('Error deleting product:', err);
    }
  };

  const deleteVariant = async (productId, variantId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta variante?')) return;

    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/products/${productId}/variants/${variantId}`, {
        method: 'DELETE',
        headers
      });

      if (response.ok) {
        await loadProductDetails(productId);
        loadProducts();
      }
    } catch (err) {
      console.error('Error deleting variant:', err);
    }
  };

  const getStockStatus = (product) => {
    if (product.has_out_of_stock) return 'out-of-stock';
    if (product.has_low_stock) return 'low-stock';
    return 'in-stock';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

  if (loading) {
    return <div className="inventory-page"><p>Cargando...</p></div>;
  }

  return (
    <div className="inventory-page">
      <header>
        <div className="logo">⚙️ Admin - FashionVision</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button className="nav-active" onClick={() => {}}>Inventario</button>
        </nav>
      </header>

      <main className="inventory-container">
        <div className="inventory-tabs">
          <button
            className={activeTab === 'products' ? 'active' : ''}
            onClick={() => setActiveTab('products')}
          >
            Productos
          </button>
          <button
            className={activeTab === 'lowstock' ? 'active' : ''}
            onClick={() => setActiveTab('lowstock')}
          >
            Stock Bajo ({lowStockItems.length})
          </button>
        </div>

        {activeTab === 'products' && (
          <>
            <div className="inventory-toolbar">
              <div className="search-box">
                <input
                  type="text"
                  placeholder="Buscar productos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="">Todas las categorías</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              {isAdmin && (
                <button className="btn-primary" onClick={() => openProductModal()}>
                  + Nuevo Producto
                </button>
              )}
            </div>

            <div className="products-table-wrapper">
              <table className="products-table">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>SKU</th>
                    <th>Categoría</th>
                    <th>Precio</th>
                    <th>Variantes</th>
                    <th>Stock Total</th>
                    <th>Estado</th>
                    {isAdmin && <th>Acciones</th>}
                  </tr>
                </thead>
                <tbody>
                  {products.map(product => (
                    <tr key={product.id}>
                      <td><strong>{product.name}</strong></td>
                      <td>{product.sku}</td>
                      <td>{categories.find(c => c.id === product.category_id)?.name || '-'}</td>
                      <td>{formatCurrency(product.base_price)}</td>
                      <td>{product.variants_count}</td>
                      <td className={getStockStatus(product)}>
                        {product.total_stock} unidades
                      </td>
                      <td>
                        <span className={`status-badge ${getStockStatus(product)}`}>
                          {product.has_out_of_stock ? 'Agotado' :
                           product.has_low_stock ? 'Stock Bajo' : 'Disponible'}
                        </span>
                      </td>
                      {isAdmin && (
                        <td>
                          <div className="action-buttons">
                            <button className="btn-icon" onClick={() => handleViewProduct(product)} title="Ver">👁️</button>
                            <button className="btn-icon" onClick={() => openProductModal(product)} title="Editar">✏️</button>
                            <button className="btn-icon btn-danger" onClick={() => deleteProduct(product.id)} title="Eliminar">🗑️</button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                  {products.length === 0 && (
                    <tr>
                      <td colSpan={isAdmin ? 8 : 7} className="empty-row">
                        No se encontraron productos
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTab === 'lowstock' && (
          <div className="alerts-list">
            {lowStockItems.map(item => (
              <div key={item.variant_id} className={`alert-item ${item.status}`}>
                <div className="alert-info">
                  <strong>{item.product_name}</strong>
                  <span>{item.size || 'Talla única'} - {item.color || 'Color único'}</span>
                  <span className="sku">SKU: {item.sku_variant}</span>
                </div>
                <div className="alert-stock">
                  <span className={`stock-badge ${item.status}`}>
                    {item.status === 'out_of_stock' ? 'AGOTADO' : 'STOCK BAJO'}
                  </span>
                  <span className="stock-count">
                    {item.quantity_available} disponibles
                    {item.quantity_reserved > 0 && ` (${item.quantity_reserved} reservadas)`}
                  </span>
                  <span className="threshold">Mínimo: {item.low_stock_threshold}</span>
                </div>
                {isAdmin && (
                  <button
                    className="btn-small"
                    onClick={() => {
                      const product = products.find(p => p.id === item.product_id);
                      if (product) {
                        openStockModal(product, item);
                      }
                    }}
                  >
                    Reabastecer
                  </button>
                )}
              </div>
            ))}
            {lowStockItems.length === 0 && (
              <p className="no-alerts">No hay alertas de inventario</p>
            )}
          </div>
        )}
      </main>

      {showProductModal && (
        <ProductModalForm
          product={editingProduct}
          productData={productForm}
          setProductData={setProductForm}
          selectedProduct={selectedProduct}
          categories={categories}
          isAdmin={isAdmin}
          onSubmit={handleProductSubmit}
          onClose={closeProductModal}
          onOpenVariant={openVariantModal}
          onOpenStock={openStockModal}
          onImageUpload={handleImageUpload}
          onImageDelete={handleImageDelete}
          onDeleteVariant={deleteVariant}
          error={error}
          formatCurrency={formatCurrency}
        />
      )}

      {showVariantModal && (
        <VariantModalForm
          variant={editingVariant}
          variantData={variantForm}
          setVariantData={setVariantForm}
          onSubmit={handleVariantSubmit}
          onClose={closeVariantModal}
          error={error}
        />
      )}

      {showStockModal && (
        <StockModalForm
          product={selectedProduct}
          variant={selectedVariant}
          stockData={stockForm}
          setStockData={setStockForm}
          movements={movements}
          onSubmit={handleStockSubmit}
          onClose={closeStockModal}
          error={error}
        />
      )}
    </div>
  );
};

function ProductModalForm({
  product, productData, setProductData, selectedProduct, categories, isAdmin,
  onSubmit, onClose, onOpenVariant, onOpenStock, onImageUpload, onImageDelete,
  onDeleteVariant, error, formatCurrency
}) {
  const isEditMode = !!product;
  const isViewMode = !!selectedProduct && !isEditMode;
  const displayProduct = selectedProduct || product;

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file && displayProduct?.id) {
      await onImageUpload(displayProduct.id, file);
    }
  };

  if (!isViewMode) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content product-modal" onClick={e => e.stopPropagation()}>
          <h2>{isEditMode ? 'Editar Producto' : 'Nuevo Producto'}</h2>
          <form onSubmit={onSubmit}>
            {error && <div className="error-message">{error}</div>}
            <div className="form-grid">
              <div className="form-group">
                <label>Nombre</label>
                <input
                  type="text"
                  value={productData.name}
                  onChange={e => setProductData({ ...productData, name: e.target.value })}
                  required
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>SKU</label>
                <input
                  type="text"
                  value={productData.sku}
                  onChange={e => setProductData({ ...productData, sku: e.target.value })}
                  required
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Precio Base</label>
                <input
                  type="number"
                  step="0.01"
                  value={productData.base_price}
                  onChange={e => setProductData({ ...productData, base_price: e.target.value })}
                  required
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Categoría</label>
                <select
                  value={productData.category_id}
                  onChange={e => setProductData({ ...productData, category_id: e.target.value })}
                  disabled={!isAdmin}
                >
                  <option value="">Seleccionar categoría</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group full-width">
                <label>Descripción</label>
                <textarea
                  value={productData.description}
                  onChange={e => setProductData({ ...productData, description: e.target.value })}
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group full-width">
                <label>Clase YOLO</label>
                <input
                  type="text"
                  value={productData.yolo_class_name}
                  onChange={e => setProductData({ ...productData, yolo_class_name: e.target.value })}
                  placeholder="Ej: gorra-roja-lacoste"
                  disabled={!isAdmin}
                />
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
              {isAdmin && <button type="submit" className="btn-primary">{isEditMode ? 'Actualizar' : 'Crear'}</button>}
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content product-modal large" onClick={e => e.stopPropagation()}>
        <h2>{displayProduct.name}</h2>
        {error && <div className="error-message">{error}</div>}

        <div className="product-detail-grid">
          <div className="product-info-section">
            <div className="info-row"><span className="label">SKU:</span><span className="value">{displayProduct.sku}</span></div>
            <div className="info-row"><span className="label">Precio:</span><span className="value">{formatCurrency(displayProduct.base_price)}</span></div>
            <div className="info-row"><span className="label">Categoría:</span><span className="value">{categories.find(c => c.id === displayProduct.category_id)?.name || '-'}</span></div>
            {displayProduct.yolo_class_name && (
              <div className="info-row"><span className="label">YOLO Class:</span><span className="value">{displayProduct.yolo_class_name}</span></div>
            )}
            {displayProduct.description && (
              <div className="info-row"><span className="label">Descripción:</span><span className="value">{displayProduct.description}</span></div>
            )}
          </div>

          {isAdmin && (
            <div className="product-images-section">
              <h4>Imágenes</h4>
              <div className="images-grid">
                {(displayProduct.images || []).map((img, idx) => (
                  <div key={idx} className="image-item">
                    <img src={img} alt="" />
                    <button type="button" className="btn-delete-image" onClick={() => onImageDelete(displayProduct.id, img)}>×</button>
                  </div>
                ))}
              </div>
              <label className="upload-image-btn">
                <input type="file" accept="image/*" onChange={handleFileChange} />
                + Agregar Imagen
              </label>
            </div>
          )}
        </div>

        <div className="variants-section">
          <div className="variants-header">
            <h4>Variantes</h4>
            {isAdmin && displayProduct.id && (
              <button type="button" className="btn-small" onClick={() => onOpenVariant(displayProduct)}>
                + Nueva Variante
              </button>
            )}
          </div>

          {displayProduct.variants?.length > 0 ? (
            <table className="variants-table">
              <thead>
                <tr>
                  <th>Talla</th><th>Color</th><th>SKU Variante</th><th>Modifier</th><th>Stock</th><th>Estado</th>
                  {isAdmin && <th>Acciones</th>}
                </tr>
              </thead>
              <tbody>
                {displayProduct.variants.map(v => (
                  <tr key={v.id}>
                    <td>{v.size || '-'}</td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {v.color_hex && <span style={{ width: '16px', height: '16px', backgroundColor: v.color_hex, borderRadius: '3px', border: '1px solid #ddd' }} />}
                        {v.color || '-'}
                      </span>
                    </td>
                    <td>{v.sku_variant}</td>
                    <td>{v.price_modifier > 0 ? `+${v.price_modifier}` : v.price_modifier}</td>
                    <td className={v.inventory?.quantity_available === 0 ? 'out-of-stock' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'low-stock' : ''}>
                      {v.inventory?.quantity_available || 0}
                    </td>
                    <td>
                      <span className={`status-badge ${v.inventory?.quantity_available === 0 ? 'out-of-stock' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'low-stock' : 'in-stock'}`}>
                        {v.inventory?.quantity_available === 0 ? 'Agotado' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'Bajo' : 'OK'}
                      </span>
                    </td>
                    {isAdmin && (
                      <td>
                        <div className="action-buttons">
                          <button className="btn-icon" onClick={() => onOpenVariant(displayProduct, v)} title="Editar">✏️</button>
                          <button className="btn-icon" onClick={() => onOpenStock(displayProduct, v)} title="Stock">📦</button>
                          <button className="btn-icon btn-danger" onClick={() => onDeleteVariant(displayProduct.id, v.id)} title="Eliminar">🗑️</button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="no-variants">No hay variantes definidas</p>
          )}
        </div>

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}

function VariantModalForm({ variant, variantData, setVariantData, onSubmit, onClose, error }) {
  const isEditMode = !!variant;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>{isEditMode ? 'Editar Variante' : 'Nueva Variante'}</h2>
        <form onSubmit={onSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-grid">
            <div className="form-group">
              <label>Talla</label>
              <input type="text" value={variantData.size} onChange={e => setVariantData({ ...variantData, size: e.target.value })} placeholder="Ej: M, L, XL" />
            </div>
            <div className="form-group">
              <label>Color</label>
              <input type="text" value={variantData.color} onChange={e => setVariantData({ ...variantData, color: e.target.value })} placeholder="Ej: Azul" />
            </div>
            <div className="form-group">
              <label>Color Hex</label>
              <input type="color" value={variantData.color_hex} onChange={e => setVariantData({ ...variantData, color_hex: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Modifier de Precio</label>
              <input type="number" step="0.01" value={variantData.price_modifier} onChange={e => setVariantData({ ...variantData, price_modifier: e.target.value })} />
            </div>
            <div className="form-group full-width">
              <label>SKU Variante</label>
              <input type="text" value={variantData.sku_variant} onChange={e => setVariantData({ ...variantData, sku_variant: e.target.value })} required />
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">{isEditMode ? 'Actualizar' : 'Crear'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function StockModalForm({ product, variant, stockData, setStockData, movements, onSubmit, onClose, error }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content stock-modal" onClick={e => e.stopPropagation()}>
        <h2>Ajuste de Inventario</h2>
        <div className="stock-product-info">
          <strong>{product?.name}</strong>
          <span>{variant?.size || 'Talla única'} - {variant?.color || 'Color único'}</span>
          <span className="sku">SKU: {variant?.sku_variant}</span>
          <span className="current-stock">Stock actual: <strong>{variant?.quantity_available || 0}</strong></span>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={onSubmit} className="stock-form">
          <div className="form-group">
            <label>Tipo de operación</label>
            <select value={stockData.type} onChange={e => setStockData({ ...stockData, type: e.target.value })}>
              <option value="restock">Reabastecer (+)</option>
              <option value="adjust">Ajuste (±)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Cantidad</label>
            <input type="number" value={stockData.quantity} onChange={e => setStockData({ ...stockData, quantity: e.target.value })} required />
          </div>
          <div className="form-group full-width">
            <label>Notas / Razón</label>
            <textarea value={stockData.reason} onChange={e => setStockData({ ...stockData, reason: e.target.value })} placeholder="Ej: Entrada de mercancía..." />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">Confirmar</button>
          </div>
        </form>

        {movements.length > 0 && (
          <div className="movements-section">
            <h4>Historial de Movimientos</h4>
            <div className="movements-list">
              {movements.slice(0, 10).map(m => (
                <div key={m.id} className="movement-item">
                  <span className="movement-type">{m.movement_type}</span>
                  <span className={`movement-qty ${m.quantity_change > 0 ? 'positive' : 'negative'}`}>
                    {m.quantity_change > 0 ? '+' : ''}{m.quantity_change}
                  </span>
                  <span className="movement-date">{formatLocalDateTime(m.created_at)}</span>
                  {m.notes && <span className="movement-notes">{m.notes}</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Inventory;