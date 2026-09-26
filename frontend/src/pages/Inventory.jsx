import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHeaders, getCategories, getLowStockProducts, getInventoryMovements,
         getSuppliers, updateInventoryStatus, getPriceBreakdown,
         getProductPriceHistory, performLogout, reactivateAttribute,
         getAttributesWithStock, getAttributeProducts } from '../services/api';
import { generateEmbedding } from '../services/catalogService';
import { formatLocalDateTime } from '../utils/dateUtils';
import '../styles/Inventory.css';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

const STOCK_STATUSES = ['available', 'reserved', 'damaged', 'in_transit', 'returned'];
const STOCK_STATUS_LABELS = {
  available: 'Disponible',
  reserved: 'Reservado',
  damaged: 'Dañado',
  in_transit: 'En tránsito',
  returned: 'Devuelto'
};

const Inventory = () => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showFeaturedOnly, setShowFeaturedOnly] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [showAttributeModal, setShowAttributeModal] = useState(false);
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [showPriceBreakdownModal, setShowPriceBreakdownModal] = useState(false);
  const [showAttributeProductsModal, setShowAttributeProductsModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingVariant, setEditingVariant] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [movements, setMovements] = useState([]);
  const [error, setError] = useState('');
  const [attributesWithStock, setAttributesWithStock] = useState([]);
  const [showInactiveAttributes, setShowInactiveAttributes] = useState(false);
  const [activeAttributeTab, setActiveAttributeTab] = useState('sizes');
  const [selectedAttribute, setSelectedAttribute] = useState(null);
  const [attributeProducts, setAttributeProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [priceBreakdown, setPriceBreakdown] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [availableSizes, setAvailableSizes] = useState([]);
  const [availableColors, setAvailableColors] = useState([]);

  const [productForm, setProductForm] = useState({
    name: '',
    sku: '',
    base_price: '',
    cost_price: '',
    tax_rate: '0.16',
    profit_margin: '',
    brand: '',
    supplier: '',
    barcode: '',
    weight: '',
    width: '',
    height: '',
    depth: '',
    is_featured: false,
    tags: [],
    description: '',
    category_id: '',
    images: []
  });

  const [variantForm, setVariantForm] = useState({
    size_attribute_id: null,
    color_attribute_id: null,
    color_hex: '#000000',
    sku_variant: ''
  });

  const [stockForm, setStockForm] = useState({
    quantity: '',
    reason: '',
    type: 'restock',
    stock_status: 'available',
    warehouse_location: ''
  });

  const [attributeForm, setAttributeForm] = useState({
    type: 'size',
    value: '',
    hex_code: '#000000'
  });

  const [supplierForm, setSupplierForm] = useState({
    name: '',
    contact_name: '',
    email: '',
    phone: '',
    address: ''
  });

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState('');
  const [stockSuccess, setStockSuccess] = useState('');
  const [variantSuccess, setVariantSuccess] = useState('');

  const isAdmin = userData?.role === 'admin';

  const handleLogout = () => {
    performLogout();
    navigate('/');
  };

  const loadProducts = useCallback(async () => {
    try {
      const headers = getHeaders();
      const params = new URLSearchParams();
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (selectedCategory) params.append('category_id', selectedCategory);
      if (showFeaturedOnly) params.append('is_featured', 'true');

      const response = await fetch(`${API_URL}/api/products/stock/all?${params}`, { headers });
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (err) {
      console.error('Error loading products:', err);
    }
  }, [debouncedSearch, selectedCategory, showFeaturedOnly]);

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

  const loadAttributes = useCallback(async () => {
    try {
      const stockData = await getAttributesWithStock(null, showInactiveAttributes);
      setAttributesWithStock(stockData.attributes || []);
      const allAttrs = stockData.attributes || [];
      setAvailableSizes(allAttrs.filter(a => a.type === 'size'));
      setAvailableColors(allAttrs.filter(a => a.type === 'color'));
    } catch (err) {
      console.error('Error loading attributes:', err);
    }
  }, [showInactiveAttributes]);

  const loadSuppliers = useCallback(async () => {
    try {
      const data = await getSuppliers(true);
      setSuppliers(data);
    } catch (err) {
      console.error('Error loading suppliers:', err);
    }
  }, []);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setUserData(user);
    if (user.role !== 'admin') {
      navigate('/');
      return;
    }
    loadData();
    loadAttributes();
    loadSuppliers();
  }, [navigate, loadData, loadAttributes, loadSuppliers]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

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

  const openProductModal = async (product = null) => {
    if (product) {
      try {
        const headers = getHeaders();

        const [productRes, stockRes] = await Promise.all([
          fetch(`${API_URL}/api/products/${product.id}`, { headers }),
          fetch(`${API_URL}/api/products/${product.id}/stock`, { headers })
        ]);

        if (!productRes.ok || !stockRes.ok) throw new Error('Error loading product');

        const fullProduct = await productRes.json();
        const stockData = await stockRes.json();

        const productWithVariants = {
          ...fullProduct,
          variants: stockData.variants || []
        };

        setEditingProduct(productWithVariants);
        setSelectedFiles([]);
        setSubmitting(false);
        setSubmitStatus('');
        setProductForm({
          name: fullProduct.name || '',
          sku: fullProduct.sku || '',
          base_price: fullProduct.base_price || '',
          cost_price: fullProduct.cost_price || '',
          tax_rate: fullProduct.tax_rate?.toString() || '0.16',
          profit_margin: fullProduct.profit_margin || '',
          brand: fullProduct.brand || '',
          supplier: fullProduct.supplier || '',
          barcode: fullProduct.barcode || '',
          weight: fullProduct.weight || '',
          width: fullProduct.width || '',
          height: fullProduct.height || '',
          depth: fullProduct.depth || '',
          is_featured: fullProduct.is_featured || false,
          tags: fullProduct.tags || [],
          description: fullProduct.description || '',
          category_id: fullProduct.category_id || '',
          images: fullProduct.images || []
        });
      } catch (err) {
        console.error('Error loading product details:', err);
        setError('Error al cargar datos del producto');
        return;
      }
    } else {
      setEditingProduct(null);
      setSelectedProduct(null);
      setSelectedFiles([]);
      setSubmitting(false);
      setSubmitStatus('');
      setProductForm({
        name: '',
        sku: '',
        base_price: '',
        cost_price: '',
        tax_rate: '0.16',
        profit_margin: '',
        brand: '',
        supplier: '',
        barcode: '',
        weight: '',
        width: '',
        height: '',
        depth: '',
        is_featured: false,
        tags: [],
        description: '',
        category_id: '',
        images: []
      });
    }
    setShowProductModal(true);
  };

  const closeProductModal = () => {
    setShowProductModal(false);
    setEditingProduct(null);
    setSelectedProduct(null);
    setSelectedFiles([]);
    setSubmitting(false);
    setSubmitStatus('');
    setError('');
    loadProducts();
    loadLowStock();
  };

  const openVariantModal = (product, variant = null) => {
    setSelectedProduct(product);
    if (variant) {
      setEditingVariant(variant);
      setVariantForm({
        size_attribute_id: variant.size_attribute_id || null,
        color_attribute_id: variant.color_attribute_id || null,
        color_hex: variant.color_hex || '#000000',
        sku_variant: variant.sku_variant
      });
    } else {
      setEditingVariant(null);
      setVariantForm({
        size_attribute_id: null,
        color_attribute_id: null,
        color_hex: '#000000',
        sku_variant: ''
      });
    }
    setShowVariantModal(true);
  };

  const closeVariantModal = () => {
    setShowVariantModal(false);
    setEditingVariant(null);
    setError('');
    setVariantSuccess('');
  };

  const openStockModal = async (product, variant) => {
    setSelectedProduct(product);
    setSelectedVariant(variant);
    setStockForm({
      quantity: '',
      reason: '',
      type: 'restock',
      stock_status: variant.stock_status || 'available',
      warehouse_location: variant.warehouse_location || ''
    });
    await loadMovements(variant.id);
    setShowStockModal(true);
  };

  const openViewProductModal = async (product) => {
    try {
      const headers = getHeaders();

      const [productRes, stockRes] = await Promise.all([
        fetch(`${API_URL}/api/products/${product.id}`, { headers }),
        fetch(`${API_URL}/api/products/${product.id}/stock`, { headers })
      ]);

      if (!productRes.ok || !stockRes.ok) throw new Error('Error loading product');

      const fullProduct = await productRes.json();
      const stockData = await stockRes.json();

      const productWithVariants = {
        ...fullProduct,
        variants: stockData.variants || []
      };

      setSelectedProduct(productWithVariants);
      setEditingProduct(null);
      setShowProductModal(true);
    } catch (err) {
      console.error('Error loading product details:', err);
      setError('Error al cargar datos del producto');
    }
  };

  const closeStockModal = () => {
    setShowStockModal(false);
    setSelectedVariant(null);
    setMovements([]);
    setError('');
    setStockSuccess('');
    if (selectedProduct?.id) {
      loadProductDetails(selectedProduct.id);
    }
    loadProducts();
    loadLowStock();
  };

  const openAttributeModal = () => {
    setAttributeForm({ type: 'size', value: '', hex_code: '#000000' });
    setShowAttributeModal(true);
  };

  const closeAttributeModal = () => {
    setShowAttributeModal(false);
    setAttributeForm({ type: 'size', value: '', hex_code: '#000000' });
    setError('');
  };

  const openAttributeProductsModal = async (attribute) => {
    setSelectedAttribute(attribute);
    setError('');
    try {
      const data = await getAttributeProducts(attribute.id);
      setAttributeProducts(data.products || []);
      setShowAttributeProductsModal(true);
    } catch (err) {
      console.error('Error loading attribute products:', err);
      setError('Error al cargar productos del atributo');
    }
  };

  const closeAttributeProductsModal = () => {
    setShowAttributeProductsModal(false);
    setSelectedAttribute(null);
    setAttributeProducts([]);
    setError('');
  };

  const openSupplierModal = () => {
    setSupplierForm({ name: '', contact_name: '', email: '', phone: '', address: '' });
    setShowSupplierModal(true);
  };

  const closeSupplierModal = () => {
    setShowSupplierModal(false);
    setSupplierForm({ name: '', contact_name: '', email: '', phone: '', address: '' });
    setError('');
  };

  const closePriceBreakdownModal = () => {
    setShowPriceBreakdownModal(false);
    setPriceBreakdown(null);
    setSelectedVariant(null);
    setError('');
  };

  const _openPriceBreakdownModal = async (product, variant = null) => {
    setSelectedProduct(product);
    setSelectedVariant(variant);
    setError('');
    try {
      const data = await getPriceBreakdown(product.id, variant?.id || null);
      setPriceBreakdown(data);
      setShowPriceBreakdownModal(true);
    } catch (err) {
      console.error('Error loading price breakdown:', err);
      setError('Error al cargar desglose de precio');
    }
  };

  const _loadPriceHistory = async (productId) => {
    try {
      const data = await getProductPriceHistory(productId, 20);
      setPriceHistory(data);
      setShowPriceHistory(true);
    } catch (err) {
      console.error('Error loading price history:', err);
      setError('Error al cargar historial de precios');
    }
  };

  const handleAttributeSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/attributes`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(attributeForm)
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al guardar atributo');
      }
      closeAttributeModal();
      loadAttributes();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSupplierSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/suppliers`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(supplierForm)
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al guardar proveedor');
      }
      closeSupplierModal();
      loadSuppliers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStockStatusUpdate = async () => {
    if (!selectedVariant?.id) return;
    setError('');
    try {
      await updateInventoryStatus(selectedVariant.id, {
        stock_status: stockForm.stock_status,
        warehouse_location: stockForm.warehouse_location || null
      });
      closeStockModal();
      loadProducts();
      loadLowStock();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const headers = getHeaders();
      const method = editingProduct ? 'PUT' : 'POST';
      const url = editingProduct
        ? `${API_URL}/api/products/${editingProduct.id}`
        : `${API_URL}/api/products`;

      const payload = {
        name: productForm.name,
        sku: productForm.sku,
        base_price: parseFloat(productForm.base_price) || 0,
        cost_price: parseFloat(productForm.cost_price) || 0,
        tax_rate: parseFloat(productForm.tax_rate) || 0.16,
        profit_margin: parseFloat(productForm.profit_margin) || 0,
        brand: productForm.brand || null,
        supplier: productForm.supplier || null,
        barcode: productForm.barcode || null,
        weight: parseFloat(productForm.weight) || null,
        width: parseFloat(productForm.width) || null,
        height: parseFloat(productForm.height) || null,
        depth: parseFloat(productForm.depth) || null,
        is_featured: productForm.is_featured,
        tags: productForm.tags || [],
        description: productForm.description || null,
        category_id: productForm.category_id,
        images: productForm.images || []
      };

      setSubmitStatus('Creando producto...');
      const response = await fetch(url, {
        method,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al guardar producto');
      }

      const created = await response.json();
      const productId = editingProduct?.id || created.id;

      if (selectedFiles.length > 0 && !editingProduct) {
        setSubmitStatus('Subiendo imágenes...');
        let cloudinaryOk = true;
        for (const file of selectedFiles) {
          try {
            const imgFormData = new FormData();
            imgFormData.append('file', file);
            const imgHeaders = getHeaders();
            delete imgHeaders['Content-Type'];
            await fetch(`${API_URL}/api/products/${productId}/images`, {
              method: 'POST',
              headers: imgHeaders,
              body: imgFormData
            });
          } catch (uploadErr) {
            cloudinaryOk = false;
            console.warn('Cloudinary no disponible, las imágenes no se guardarán en la galería:', uploadErr.message);
            break;
          }
        }

        setSubmitStatus('Generando embedding...');
        try {
          if (cloudinaryOk) {
            await generateEmbedding(productId, null);
          } else {
            await generateEmbedding(productId, selectedFiles);
          }
        } catch (embErr) {
          console.warn('Auto-vectorization failed:', embErr);
        }
      }

      closeProductModal();
      loadProducts();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
      setSubmitStatus('');
    }
  };

  const handleVariantSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setVariantSuccess('');

    try {
      const headers = getHeaders();
      const method = editingVariant ? 'PUT' : 'POST';
      const url = editingVariant
        ? `${API_URL}/api/products/${selectedProduct.id}/variants/${editingVariant.id}`
        : `${API_URL}/api/products/${selectedProduct.id}/variants`;

      const payload = {
        ...variantForm,
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

      setVariantSuccess(editingVariant ? 'Variante actualizada correctamente' : 'Variante creada correctamente');
      loadProducts();
      loadLowStock();
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
    setStockSuccess('');

    try {
      const headers = getHeaders();
      const isRestock = stockForm.type === 'restock';
      const payload = isRestock
        ? { quantity: parseInt(stockForm.quantity), notes: stockForm.reason }
        : { quantity_change: parseInt(stockForm.quantity), reason: stockForm.reason };

      const endpoint = isRestock
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

      const updatedInventory = await response.json();
      setSelectedVariant(prev => ({
        ...prev,
        inventory: { ...prev.inventory, quantity_available: updatedInventory.quantity_after }
      }));
      setStockForm({ quantity: '', reason: '', type: 'restock' });
      setStockSuccess('Stock actualizado correctamente');
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

  const _handleImageUpload = async (productId, file) => {
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

  const _handleImageDelete = async (productId, imageUrl) => {
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
        setProducts(products.filter(p => p.id !== productId));
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar producto');
      }
    } catch (err) {
      console.error('Error deleting product:', err);
      alert('Error al eliminar producto');
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
        loadLowStock();
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar la variante');
      }
    } catch (err) {
      console.error('Error deleting variant:', err);
      alert('Error al eliminar la variante');
    }
  };

  const deleteAttribute = async (attributeId) => {
    if (!window.confirm('¿Desactivar este atributo? (Podrás reactivarlo después)')) return;

    try {
      const headers = getHeaders();
      const response = await fetch(`${API_URL}/api/attributes/${attributeId}`, {
        method: 'DELETE',
        headers
      });

      if (response.ok) {
        loadAttributes();
      }
    } catch (err) {
      console.error('Error deactivating attribute:', err);
    }
  };

  const reactivateAttributeFn = async (attributeId) => {
    try {
      await reactivateAttribute(attributeId);
      loadAttributes();
    } catch (err) {
      console.error('Error reactivating attribute:', err);
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
          <button onClick={() => navigate('/admin/catalog')}>Catálogo</button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
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
          <button
            className={activeTab === 'attributes' ? 'active' : ''}
            onClick={() => { setActiveTab('attributes'); loadAttributes(); }}
          >
            Atributos
          </button>
          <button
            className={activeTab === 'suppliers' ? 'active' : ''}
            onClick={() => { setActiveTab('suppliers'); loadSuppliers(); }}
          >
            Proveedores
          </button>
        </div>

        {activeTab === 'products' && (
          <>
            <div className="inventory-toolbar">
              <div className="search-box">
                <input
                  type="text"
                  placeholder="Buscar por nombre o barcode..."
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
              <label className="featured-filter">
                <input
                  type="checkbox"
                  checked={showFeaturedOnly}
                  onChange={(e) => setShowFeaturedOnly(e.target.checked)}
                />
                Solo destacados
              </label>
              <span className="featured-info-tip" title="Los productos destacados se calculan automáticamente cada hora según las ventas del mes (top 3 por categoría, mínimo 5 ventas)">
                ⓘ Auto
              </span>
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
                    <th>⭐</th>
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
                      <td>{product.is_featured ? '⭐' : ''}</td>
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
                            <button className="btn-text" onClick={() => openViewProductModal(product)}>Ver</button>
                            <button className="btn-text" onClick={() => openProductModal(product)}>Editar</button>
                            <button className="btn-text btn-danger" onClick={() => deleteProduct(product.id)}>Eliminar</button>
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
                  <span>{item.size_value || 'Talla única'} - {item.color_value || 'Color único'}</span>
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
                        const mappedVariant = {
                          ...item,
                          id: item.variant_id,
                          size_attribute: { value: item.size_value || null },
                          color_attribute: { value: item.color_value || null }
                        };
                        openStockModal(product, mappedVariant);
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

        {activeTab === 'attributes' && (
          <div className="attributes-section">
            <div className="section-header">
              <div className="attributes-title-row">
                <h3 className="attributes-title">Atributos</h3>
                <p className="attributes-subtitle">Tallas y Colores disponibles en el sistema</p>
              </div>
              <div className="attributes-controls">
                <label className="show-inactive-filter">
                  <input
                    type="checkbox"
                    checked={showInactiveAttributes}
                    onChange={(e) => {
                      setShowInactiveAttributes(e.target.checked);
                    }}
                  />
                  Ver desactivados
                </label>
                {isAdmin && (
                  <button className="btn-primary" onClick={openAttributeModal}>+ Nuevo Atributo</button>
                )}
              </div>
            </div>

            <div className="attributes-tabs">
              <button
                className={`attr-tab ${activeAttributeTab === 'sizes' ? 'active' : ''}`}
                onClick={() => setActiveAttributeTab('sizes')}
              >
                Tallas ({attributesWithStock.filter(a => a.type === 'size').length})
              </button>
              <button
                className={`attr-tab ${activeAttributeTab === 'colors' ? 'active' : ''}`}
                onClick={() => setActiveAttributeTab('colors')}
              >
                Colores ({attributesWithStock.filter(a => a.type === 'color').length})
              </button>
            </div>

            {activeAttributeTab === 'sizes' && (
              <div className="attribute-group">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Valor</th>
                      <th>Stock</th>
                      <th>Productos</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attributesWithStock.filter(a => a.type === 'size').map(attr => (
                      <tr key={attr.id} className={!attr.is_active ? 'inactive-row' : ''}>
                        <td><span className={!attr.is_active ? 'text-inactive' : ''}>{attr.value}</span></td>
                        <td>
                          <span className={`stock-count ${attr.total_stock === 0 ? 'no-stock' : ''}`}>
                            {attr.total_stock}
                          </span>
                        </td>
                        <td>
                          <span className="products-count">{attr.products_count || 0}</span>
                        </td>
                        <td>
                          <span className={`status-badge ${
                            !attr.is_active ? 'inactive' :
                            attr.is_effective ? 'active' : 'no-stock'
                          }`}>
                            {!attr.is_active ? 'Desactivado' :
                             attr.is_effective ? 'Activo' : 'Sin Stock'}
                          </span>
                        </td>
                        <td>
                          {isAdmin && (
                            <div className="action-buttons">
                              <button
                                className="btn-text btn-info"
                                onClick={() => openAttributeProductsModal(attr)}
                                disabled={!attr.products_count}
                                title={!attr.products_count ? 'Sin productos asignados' : ''}
                              >
                                Ver Productos
                              </button>
                              {attr.is_active ? (
                                <button className="btn-text btn-warning" onClick={() => deleteAttribute(attr.id)}>Desactivar</button>
                              ) : (
                                <button className="btn-text btn-success" onClick={() => reactivateAttributeFn(attr.id)}>Reactivar</button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                    {attributesWithStock.filter(a => a.type === 'size').length === 0 && (
                      <tr><td colSpan="5" className="no-data-cell">No hay tallas registradas</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeAttributeTab === 'colors' && (
              <div className="attribute-group">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Color</th>
                      <th>Valor</th>
                      <th>Stock</th>
                      <th>Productos</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attributesWithStock.filter(a => a.type === 'color').map(attr => (
                      <tr key={attr.id} className={!attr.is_active ? 'inactive-row' : ''}>
                        <td><span className="color-swatch" style={{ backgroundColor: attr.hex_code || '#000' }} /></td>
                        <td><span className={!attr.is_active ? 'text-inactive' : ''}>{attr.value}</span></td>
                        <td>
                          <span className={`stock-count ${attr.total_stock === 0 ? 'no-stock' : ''}`}>
                            {attr.total_stock}
                          </span>
                        </td>
                        <td>
                          <span className="products-count">{attr.products_count || 0}</span>
                        </td>
                        <td>
                          <span className={`status-badge ${
                            !attr.is_active ? 'inactive' :
                            attr.is_effective ? 'active' : 'no-stock'
                          }`}>
                            {!attr.is_active ? 'Desactivado' :
                             attr.is_effective ? 'Activo' : 'Sin Stock'}
                          </span>
                        </td>
                        <td>
                          {isAdmin && (
                            <div className="action-buttons">
                              <button
                                className="btn-text btn-info"
                                onClick={() => openAttributeProductsModal(attr)}
                                disabled={!attr.products_count}
                                title={!attr.products_count ? 'Sin productos asignados' : ''}
                              >
                                Ver Productos
                              </button>
                              {attr.is_active ? (
                                <button className="btn-text btn-warning" onClick={() => deleteAttribute(attr.id)}>Desactivar</button>
                              ) : (
                                <button className="btn-text btn-success" onClick={() => reactivateAttributeFn(attr.id)}>Reactivar</button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                    {attributesWithStock.filter(a => a.type === 'color').length === 0 && (
                      <tr><td colSpan="6" className="no-data-cell">No hay colores registrados</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'suppliers' && (
          <div className="suppliers-section">
            <div className="section-header">
              <h3>Proveedores</h3>
              {isAdmin && (
                <button className="btn-primary" onClick={openSupplierModal}>+ Nuevo Proveedor</button>
              )}
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Contacto</th>
                  <th>Email</th>
                  <th>Teléfono</th>
                  <th>Dirección</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map(supplier => (
                  <tr key={supplier.id}>
                    <td><strong>{supplier.name}</strong></td>
                    <td>{supplier.contact_name || '-'}</td>
                    <td>{supplier.email || '-'}</td>
                    <td>{supplier.phone || '-'}</td>
                    <td>{supplier.address || '-'}</td>
                  </tr>
                ))}
                {suppliers.length === 0 && (
                  <tr><td colSpan="5" className="no-data-cell">No hay proveedores registrados</td></tr>
                )}
              </tbody>
            </table>
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
          onDeleteVariant={deleteVariant}
          error={error}
          formatCurrency={formatCurrency}
          selectedFiles={selectedFiles}
          onFilesSelected={setSelectedFiles}
          submitting={submitting}
          submitStatus={submitStatus}
          suppliers={suppliers}
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
          sizes={availableSizes}
          colors={availableColors}
          productSku={selectedProduct?.sku || ''}
          success={variantSuccess}
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
          onStatusUpdate={handleStockStatusUpdate}
          error={error}
          success={stockSuccess}
        />
      )}

      {showAttributeModal && (
        <AttributeModalForm
          attributeData={attributeForm}
          setAttributeData={setAttributeForm}
          onSubmit={handleAttributeSubmit}
          onClose={closeAttributeModal}
          error={error}
        />
      )}

      {showAttributeProductsModal && selectedAttribute && (
        <AttributeProductsModal
          attribute={selectedAttribute}
          products={attributeProducts}
          onClose={closeAttributeProductsModal}
        />
      )}

      {showSupplierModal && (
        <SupplierModalForm
          supplierData={supplierForm}
          setSupplierData={setSupplierForm}
          onSubmit={handleSupplierSubmit}
          onClose={closeSupplierModal}
          error={error}
        />
      )}

      {showPriceBreakdownModal && (
        <PriceBreakdownModal
          breakdown={priceBreakdown}
          onClose={closePriceBreakdownModal}
          formatCurrency={formatCurrency}
        />
      )}

      {showPriceHistory && (
        <div className="modal-overlay" onClick={() => setShowPriceHistory(false)}>
          <div className="modal-content price-history-modal" onClick={e => e.stopPropagation()}>
            <h2>Historial de Precios</h2>
            {error && <div className="error-message">{error}</div>}
            {priceHistory.length > 0 ? (
              <table className="price-history-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Tipo</th>
                    <th>Precio Anterior</th>
                    <th>Nuevo Precio</th>
                    <th>Notas</th>
                  </tr>
                </thead>
                <tbody>
                  {priceHistory.map((item) => (
                    <tr key={item.id}>
                      <td>{formatLocalDateTime(item.created_at)}</td>
                      <td><span className={`price-type-badge ${item.price_type}`}>{item.price_type}</span></td>
                      <td>{item.old_price ? formatCurrency(item.old_price) : '-'}</td>
                      <td>{formatCurrency(item.new_price)}</td>
                      <td>{item.reason || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">No hay historial de precios</p>
            )}
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setShowPriceHistory(false)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function ProductModalForm({
  product, productData, setProductData, selectedProduct, categories, isAdmin,
  onSubmit, onClose, onOpenVariant, onOpenStock,
  onDeleteVariant, error, formatCurrency,
  selectedFiles, onFilesSelected, submitting, submitStatus, suppliers = []
}) {
  const isEditMode = !!product;
  const isViewMode = !!selectedProduct && !isEditMode;
  const displayProduct = selectedProduct || product;

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
                  onChange={e => {
                    const newBase = e.target.value;
                    const cost = parseFloat(productData.cost_price) || 0;
                    const base = parseFloat(newBase) || 0;
                    const autoMargin = cost > 0 ? ((base - cost) / cost).toFixed(4) : productData.profit_margin;
                    setProductData({ ...productData, base_price: newBase, profit_margin: autoMargin });
                  }}
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
              <div className="form-group">
                <label>Precio de Costo</label>
                <input
                  type="number"
                  step="0.01"
                  value={productData.cost_price}
                  onChange={e => {
                    const newCost = e.target.value;
                    const cost = parseFloat(newCost) || 0;
                    const margin = parseFloat(productData.profit_margin) || 0;
                    const autoPrice = (cost * (1 + margin)).toFixed(2);
                    setProductData({ ...productData, cost_price: newCost, base_price: autoPrice });
                  }}
                  placeholder="0.00"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Margen de Ganancia (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={productData.profit_margin}
                  onChange={e => {
                    const newMargin = e.target.value;
                    const cost = parseFloat(productData.cost_price) || 0;
                    const margin = parseFloat(newMargin) || 0;
                    const autoPrice = (cost * (1 + margin)).toFixed(2);
                    setProductData({ ...productData, profit_margin: newMargin, base_price: autoPrice });
                  }}
                  placeholder="0.30 = 30%"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Tasa de IVA</label>
                <input
                  type="number"
                  step="0.0001"
                  value={productData.tax_rate}
                  onChange={e => setProductData({ ...productData, tax_rate: e.target.value })}
                  placeholder="0.16 = 16%"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Marca</label>
                <input
                  type="text"
                  value={productData.brand}
                  onChange={e => setProductData({ ...productData, brand: e.target.value })}
                  placeholder="Ej: Lacoste"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Proveedor</label>
                <select
                  value={productData.supplier}
                  onChange={e => setProductData({ ...productData, supplier: e.target.value })}
                  disabled={!isAdmin}
                >
                  <option value="">Seleccionar proveedor...</option>
                  {suppliers.map(sup => (
                    <option key={sup.id} value={sup.name}>{sup.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Barcode</label>
                <input
                  type="text"
                  value={productData.barcode}
                  onChange={e => setProductData({ ...productData, barcode: e.target.value })}
                  placeholder="Código de barras"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Peso (kg)</label>
                <input
                  type="number"
                  step="0.01"
                  value={productData.weight}
                  onChange={e => setProductData({ ...productData, weight: e.target.value })}
                  placeholder="0.5"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Ancho (cm)</label>
                <input
                  type="number"
                  step="0.1"
                  value={productData.width}
                  onChange={e => setProductData({ ...productData, width: e.target.value })}
                  placeholder="30"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Alto (cm)</label>
                <input
                  type="number"
                  step="0.1"
                  value={productData.height}
                  onChange={e => setProductData({ ...productData, height: e.target.value })}
                  placeholder="40"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Profundidad (cm)</label>
                <input
                  type="number"
                  step="0.1"
                  value={productData.depth}
                  onChange={e => setProductData({ ...productData, depth: e.target.value })}
                  placeholder="5"
                  disabled={!isAdmin}
                />
              </div>
              <div className="form-group">
                <label>Tags (separados por coma)</label>
                <input
                  type="text"
                  value={Array.isArray(productData.tags) ? productData.tags.join(', ') : productData.tags}
                  onChange={e => setProductData({ ...productData, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) })}
                  placeholder="tag1, tag2, tag3"
                  disabled={!isAdmin}
                />
              </div>
            </div>
            {isEditMode && (
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
                        <th>Talla</th><th>Color</th><th>SKU Variante</th><th>Stock</th><th>Estado</th>
                        {isAdmin && <th>Acciones</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {displayProduct.variants.map(v => (
                        <tr key={v.id}>
                          <td>{v.size_attribute?.value || '-'}</td>
                          <td>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {v.color_hex && <span style={{ width: '16px', height: '16px', backgroundColor: v.color_hex, borderRadius: '3px', border: '1px solid #ddd' }} />}
                              {v.color_attribute?.value || '-'}
                            </span>
                          </td>
                          <td>{v.sku_variant}</td>
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
                              <div className="variant-actions">
                                <button className="btn-text" onClick={() => onOpenVariant(displayProduct, v)}>Editar</button>
                                <button className="btn-text" onClick={() => onOpenStock(displayProduct, v)}>Stock</button>
                                <button className="btn-text btn-danger" onClick={() => onDeleteVariant(displayProduct.id, v.id)}>Eliminar</button>
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
            )}
            {isAdmin && !isEditMode && (
              <div className="product-images-upload-section">
                <h4>Imágenes del producto (1-5)</h4>
                <p className="field-hint">Formatos: JPEG, PNG, WebP. Las imágenes se subirán a Cloudinary y se usaran para vectorizar automáticamente el producto.</p>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  multiple
                  onChange={e => onFilesSelected(Array.from(e.target.files))}
                  disabled={submitting}
                />
                {selectedFiles && selectedFiles.length > 0 && (
                  <div className="file-chips">
                    {selectedFiles.map((f, i) => (
                      <span key={i} className="file-chip">{f.name}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
              {isAdmin && (
                submitting ? (
                  <button type="button" className="btn-primary" disabled>
                    {submitStatus || 'Procesando...'}
                  </button>
                ) : (
                  <button type="submit" className="btn-primary">
                    {isEditMode ? 'Actualizar' : 'Crear y Vectorizar'}
                  </button>
                )
              )}
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
            <div className="info-row"><span className="label">Precio de Venta:</span><span className="value">{formatCurrency(displayProduct.base_price)}</span></div>
            {displayProduct.cost_price > 0 && (
              <div className="info-row"><span className="label">Precio de Costo:</span><span className="value">{formatCurrency(displayProduct.cost_price)}</span></div>
            )}
            {/* TODO: Enable price history when needed */}
            {/* <button
              type="button"
              className="btn-info"
              onClick={() => onLoadPriceHistory(displayProduct.id)}
              style={{ marginBottom: '10px' }}
            >
              Ver Historial de Precios
            </button> */}
            {displayProduct.profit_margin > 0 && (
              <div className="info-row"><span className="label">Margen:</span><span className="value">{(displayProduct.profit_margin * 100).toFixed(1)}%</span></div>
            )}
            {displayProduct.brand && (
              <div className="info-row"><span className="label">Marca:</span><span className="value">{displayProduct.brand}</span></div>
            )}
            {displayProduct.supplier && (
              <div className="info-row"><span className="label">Proveedor:</span><span className="value">{displayProduct.supplier}</span></div>
            )}
            {displayProduct.barcode && (
              <div className="info-row"><span className="label">Barcode:</span><span className="value">{displayProduct.barcode}</span></div>
            )}
            <div className="info-row"><span className="label">Categoría:</span><span className="value">{categories.find(c => c.id === displayProduct.category_id)?.name || '-'}</span></div>
            {displayProduct.description && (
              <div className="info-row"><span className="label">Descripción:</span><span className="value">{displayProduct.description}</span></div>
            )}
            {(displayProduct.weight || displayProduct.width || displayProduct.height || displayProduct.depth) && (
              <div className="info-row">
                <span className="label">Dimensiones:</span>
                <span className="value dimensions-value">
                  {displayProduct.width && <span>Ancho: {displayProduct.width}cm</span>}
                  {displayProduct.height && <span>Alto: {displayProduct.height}cm</span>}
                  {displayProduct.depth && <span>Fondo: {displayProduct.depth}cm</span>}
                  {displayProduct.weight && <span>Peso: {displayProduct.weight}kg</span>}
                </span>
              </div>
            )}
          </div>

          {isAdmin && (
            <div className="product-images-section">
              <h4>Imágenes</h4>
              {displayProduct.images && displayProduct.images.length > 0 ? (
                <div className="images-grid">
                  {(displayProduct.images || []).map((img, idx) => (
                    <div key={idx} className="image-item">
                      <img src={img} alt="" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-images">Sin imágenes. Use el Catálogo para gestionar imágenes.</p>
              )}
            </div>
          )}
        </div>

        <div className="variants-section">
          <div className="variants-header">
            <h4>Variantes</h4>
          </div>

          {displayProduct.variants?.length > 0 ? (
            <table className="variants-table">
              <thead>
                <tr>
                  <th>Talla</th><th>Color</th><th>SKU Variante</th><th>Stock</th><th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {displayProduct.variants.map(v => (
                  <tr key={v.id}>
                    <td>{v.size_attribute?.value || '-'}</td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {v.color_hex && <span style={{ width: '16px', height: '16px', backgroundColor: v.color_hex, borderRadius: '3px', border: '1px solid #ddd' }} />}
                        {v.color_attribute?.value || '-'}
                      </span>
                    </td>
                    <td>{v.sku_variant}</td>
                    <td className={v.inventory?.quantity_available === 0 ? 'out-of-stock' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'low-stock' : ''}>
                      {v.inventory?.quantity_available || 0}
                    </td>
                    <td>
                      <span className={`status-badge ${v.inventory?.quantity_available === 0 ? 'out-of-stock' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'low-stock' : 'in-stock'}`}>
                        {v.inventory?.quantity_available === 0 ? 'Agotado' : v.inventory?.quantity_available <= v.inventory?.low_stock_threshold ? 'Bajo' : 'OK'}
                      </span>
                    </td>
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

function VariantModalForm({ variant, variantData, setVariantData, onSubmit, onClose, error, sizes = [], colors = [], productSku = '', success }) {
  const isEditMode = !!variant;

  const handleSizeChange = (e) => {
    const sizeId = e.target.value || null;
    const sizeObj = sizeId ? sizes.find(s => s.id === sizeId) : null;
    const sizeValue = sizeObj?.value || '';
    const isNumericSize = /^\d+$/.test(sizeValue);
    const sizePart = isNumericSize ? '' : sizeValue;
    const selectedColorId = variantData.color_attribute_id;
    const colorObj = selectedColorId ? colors.find(c => c.id === selectedColorId) : null;
    const colorValue = colorObj?.value || '';
    const colorPart = colorValue ? colorValue.substring(0, 3).toUpperCase() : '';
    const autoSku = [productSku, sizePart, colorPart].filter(Boolean).join('-');
    setVariantData({ ...variantData, size_attribute_id: sizeId, sku_variant: autoSku });
  };

  const handleColorChange = (e) => {
    const colorId = e.target.value || null;
    const colorObj = colorId ? colors.find(c => c.id === colorId) : null;
    const colorValue = colorObj?.value || '';
    const colorPart = colorValue ? colorValue.substring(0, 3).toUpperCase() : '';
    const selectedSizeId = variantData.size_attribute_id;
    const sizeObj = selectedSizeId ? sizes.find(s => s.id === selectedSizeId) : null;
    const sizeValue = sizeObj?.value || '';
    const isNumericSize = /^\d+$/.test(sizeValue);
    const sizePart = isNumericSize ? '' : sizeValue;
    const autoSku = [productSku, sizePart, colorPart].filter(Boolean).join('-');
    setVariantData({ ...variantData, color_attribute_id: colorId, sku_variant: autoSku });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content variant-modal" onClick={e => e.stopPropagation()}>
        <h2>{isEditMode ? 'Editar Variante' : 'Nueva Variante'}</h2>
        <form onSubmit={onSubmit}>
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
          <div className="form-grid">
            <div className="form-group">
              <label>Talla</label>
              <select
                value={variantData.size_attribute_id || ''}
                onChange={handleSizeChange}
              >
                <option value="">Seleccionar talla...</option>
                {sizes.map(size => (
                  <option key={size.id} value={size.id}>{size.value}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Color</label>
              <select
                value={variantData.color_attribute_id || ''}
                onChange={handleColorChange}
              >
                <option value="">Seleccionar color...</option>
                {colors.map(color => (
                  <option key={color.id} value={color.id}>{color.value}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Color Hex</label>
              <input type="color" value={variantData.color_hex} onChange={e => setVariantData({ ...variantData, color_hex: e.target.value })} />
            </div>
            <div className="form-group full-width">
              <label>SKU Variante {!isEditMode && '(auto-generado)'}</label>
              <input type="text" value={variantData.sku_variant} onChange={e => setVariantData({ ...variantData, sku_variant: e.target.value })} required readOnly={!isEditMode} />
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

function StockModalForm({ product, variant, stockData, setStockData, movements, onSubmit, onClose, onStatusUpdate, error, success }) {
  const [showMovements, setShowMovements] = useState(false);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content stock-modal" onClick={e => e.stopPropagation()}>
        <h2>Ajuste de Inventario</h2>
        <div className="stock-product-info">
          <strong>{product?.name}</strong>
          <span>{variant?.size_attribute?.value || 'Talla única'} - {variant?.color_attribute?.value || 'Color único'}</span>
          <span className="sku">SKU: {variant?.sku_variant}</span>
          <span className="current-stock">Stock actual: <strong>{variant?.inventory?.quantity_available || variant?.quantity_available || 0}</strong></span>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="stock-status-section">
          <h4>Estado y Ubicación</h4>
          <div className="form-grid">
            <div className="form-group">
              <label>Estado del Stock</label>
              <select value={stockData.stock_status} onChange={e => setStockData({ ...stockData, stock_status: e.target.value })}>
                <option value="available">Disponible</option>
                <option value="reserved">Reservado</option>
                <option value="damaged">Dañado</option>
                <option value="in_transit">En tránsito</option>
                <option value="returned">Devuelto</option>
              </select>
            </div>
            <div className="form-group">
              <label>Ubicación en bodega</label>
              <input type="text" value={stockData.warehouse_location} onChange={e => setStockData({ ...stockData, warehouse_location: e.target.value })} placeholder="Ej: RA-01-A1" />
            </div>
          </div>
          <button type="button" className="btn-secondary" onClick={onStatusUpdate}>Actualizar Estado</button>
        </div>

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

        <div className="stock-movements-toggle">
          <button
            type="button"
            className="btn-info"
            onClick={() => setShowMovements(!showMovements)}
          >
            {showMovements ? 'Ocultar' : 'Ver'} Historial de Movimientos ({movements.length})
          </button>
        </div>

        {showMovements && movements.length > 0 && (
          <div className="movements-section">
            <table className="movements-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Antes</th>
                  <th>Cambio</th>
                  <th>Después</th>
                  <th>Notas</th>
                </tr>
              </thead>
              <tbody>
                {movements.slice(0, 50).map(m => (
                  <tr key={m.id}>
                    <td>{formatLocalDateTime(m.created_at)}</td>
                    <td><span className={`movement-type-badge ${m.movement_type}`}>{m.movement_type}</span></td>
                    <td>{m.quantity_before}</td>
                    <td className={m.quantity_change > 0 ? 'positive' : 'negative'}>
                      {m.quantity_change > 0 ? '+' : ''}{m.quantity_change}
                    </td>
                    <td>{m.quantity_after}</td>
                    <td>{m.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {showMovements && movements.length === 0 && (
          <div className="movements-section">
            <p className="no-data">No hay movimientos registrados</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AttributeModalForm({ attributeData, setAttributeData, onSubmit, onClose, error }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Nuevo Atributo</h2>
        <form onSubmit={onSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-grid">
            <div className="form-group">
              <label>Tipo</label>
              <select value={attributeData.type} onChange={e => setAttributeData({ ...attributeData, type: e.target.value })}>
                <option value="size">Talla</option>
                <option value="color">Color</option>
              </select>
            </div>
            <div className="form-group">
              <label>Valor</label>
              <input type="text" value={attributeData.value} onChange={e => setAttributeData({ ...attributeData, value: e.target.value })} placeholder="Ej: M, L, XL, Rojo" required />
            </div>
            {attributeData.type === 'color' && (
              <div className="form-group">
                <label>Color Hex</label>
                <input type="color" value={attributeData.hex_code} onChange={e => setAttributeData({ ...attributeData, hex_code: e.target.value })} />
              </div>
            )}
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">Crear</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SupplierModalForm({ supplierData, setSupplierData, onSubmit, onClose, error }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content supplier-modal" onClick={e => e.stopPropagation()}>
        <h2>Nuevo Proveedor</h2>
        <form onSubmit={onSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-grid">
            <div className="form-group full-width">
              <label>Nombre</label>
              <input type="text" value={supplierData.name} onChange={e => setSupplierData({ ...supplierData, name: e.target.value })} placeholder="Ej: Nike" required />
            </div>
            <div className="form-group">
              <label>Nombre de contacto</label>
              <input type="text" value={supplierData.contact_name} onChange={e => setSupplierData({ ...supplierData, contact_name: e.target.value })} placeholder="Ej: Juan Pérez" />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={supplierData.email} onChange={e => setSupplierData({ ...supplierData, email: e.target.value })} placeholder="Ej: contacto@proveedor.com" />
            </div>
            <div className="form-group">
              <label>Teléfono</label>
              <input type="text" value={supplierData.phone} onChange={e => setSupplierData({ ...supplierData, phone: e.target.value })} placeholder="Ej: +52 55 1234 5678" />
            </div>
            <div className="form-group full-width">
              <label>Dirección</label>
              <textarea value={supplierData.address} onChange={e => setSupplierData({ ...supplierData, address: e.target.value })} placeholder="Ej: Av. Reforma 123, CDMX" />
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">Crear</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AttributeProductsModal({ attribute, products, onClose }) {
  if (!attribute) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content attribute-products-modal" onClick={e => e.stopPropagation()}>
        <h2>Productos que usan "{attribute.value}"</h2>
        <p className="modal-subtitle">
          {attribute.type === 'size' ? 'Talla' : 'Color'}: {attribute.value} — {products.length} producto{products.length !== 1 ? 's' : ''}
        </p>

        {products.length > 0 ? (
          <div className="attr-products-list">
            {products.map(p => (
              <div key={p.product_id} className="attr-product-card">
                <div className="attr-product-img">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.product_name} />
                  ) : (
                    <div className="no-img-placeholder">Sin imagen</div>
                  )}
                </div>
                <div className="attr-product-info">
                  <strong className="attr-product-name">{p.product_name}</strong>
                  <div className="attr-product-meta">
                    <span>SKU: {p.product_sku}</span>
                    {p.brand && <span>Marca: {p.brand}</span>}
                    <span>Categoría: {p.category_name}</span>
                    <span>Variantes con este atributo: {p.variants_using_attr}</span>
                  </div>
                  <div className="attr-product-stock">
                    <span className={`status-badge ${p.total_stock === 0 ? 'out-of-stock' : p.has_low_stock ? 'low-stock' : 'in-stock'}`}>
                      {p.total_stock === 0 ? 'Agotado' : p.has_low_stock ? 'Stock Bajo' : 'En Stock'}
                    </span>
                    <span className="stock-qty">{p.total_stock} unidades</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-data">No hay productos que usen este atributo</p>
        )}

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}

function PriceBreakdownModal({ breakdown, onClose, formatCurrency }) {
  if (!breakdown) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Desglose de Precio</h2>
        <div className="price-breakdown">
          <div className="breakdown-item">
            <span className="label">Precio de Costo:</span>
            <span className="value">{formatCurrency(breakdown.cost_price)}</span>
          </div>
          <div className="breakdown-item">
            <span className="label">Margen de Ganancia:</span>
            <span className="value">{breakdown.profit_margin_percent}%</span>
          </div>
          <div className="breakdown-item">
            <span className="label">Precio de Venta (sin IVA):</span>
            <span className="value">{formatCurrency(breakdown.selling_price)}</span>
          </div>
          <div className="breakdown-item">
            <span className="label">IVA ({breakdown.tax_rate * 100}%):</span>
            <span className="value">{formatCurrency(breakdown.tax_amount)}</span>
          </div>
          <div className="breakdown-item total">
            <span className="label">Precio Final:</span>
            <span className="value">{formatCurrency(breakdown.final_price)}</span>
          </div>
          {breakdown.variant_price_modifier !== 0 && (
            <div className="breakdown-item">
              <span className="label">Modificador de Variante:</span>
              <span className="value">{breakdown.variant_price_modifier > 0 ? '+' : ''}{formatCurrency(breakdown.variant_price_modifier)}</span>
            </div>
          )}
          <div className="breakdown-item highlight">
            <span className="label">Ganancia por unidad:</span>
            <span className="value">{formatCurrency(breakdown.total_profit)}</span>
          </div>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}

export default Inventory;