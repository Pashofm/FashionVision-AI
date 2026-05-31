import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { performLogout, getHeaders } from '../services/api';
import { getEmbeddingStatus, generateEmbedding, deleteEmbedding } from '../services/catalogService';
import '../styles/CatalogManager.css';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

const CatalogManager = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [vectorizing, setVectorizing] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const fileInputRef = useRef(null);

  const userData = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    if (userData.role !== 'admin') {
      navigate('/');
      return;
    }
    fetchStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getEmbeddingStatus();
      setProducts(data);
    } catch (err) {
      setError('Error al cargar el catálogo: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const vectorizedCount = products.filter((p) => p.has_embedding).length;
  const totalCount = products.length;
  const coveragePct = totalCount > 0 ? Math.round((vectorizedCount / totalCount) * 100) : 0;

  const openDrawer = (product) => {
    setSelectedProduct(product);
    setUploadFiles([]);
    setProgressMsg('');
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setSelectedProduct(null);
    setUploadFiles([]);
    setProgressMsg('');
  };

  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files);
    if (selected.length > 5) {
      setError('Máximo 5 imágenes permitidas');
      return;
    }
    setUploadFiles(selected);
    setError('');
  };

  const handleVectorize = async (useExisting = false) => {
    if (!selectedProduct) return;

    try {
      setVectorizing(true);
      setError('');

      if (useExisting) {
        setProgressMsg('Generando embedding desde Cloudinary...');
        await generateEmbedding(selectedProduct.product_id, null);
      } else if (uploadFiles.length > 0) {
        setProgressMsg('Subiendo imágenes a Cloudinary...');
        try {
          const headers = getHeaders();
          for (const file of uploadFiles) {
            const formData = new FormData();
            formData.append('file', file);
            const imgHeaders = { ...headers };
            delete imgHeaders['Content-Type'];
            await fetch(`${API_URL}/api/products/${selectedProduct.product_id}/images`, {
              method: 'POST',
              headers: imgHeaders,
              body: formData
            });
          }
        } catch (uploadErr) {
          console.warn('Cloudinary no disponible, las imágenes no se guardarán en la galería:', uploadErr.message);
        }

        setProgressMsg('Generando embedding...');
        await generateEmbedding(selectedProduct.product_id, uploadFiles);
      }

      setProgressMsg('');
      await fetchStatus();
      setSelectedProduct((prev) => prev ? { ...prev, has_embedding: true } : null);
      setUploadFiles([]);
    } catch (err) {
      setError('Error al vectorizar: ' + err.message);
      setProgressMsg('');
    } finally {
      setVectorizing(false);
    }
  };

  const handleDeleteEmbedding = async () => {
    if (!selectedProduct) return;
    if (!window.confirm('¿Eliminar el embedding de este producto? Dejará de ser detectable por cámara.')) return;

    try {
      setVectorizing(true);
      setError('');
      setProgressMsg('Eliminando embedding...');
      await deleteEmbedding(selectedProduct.product_id);
      await fetchStatus();
      setSelectedProduct((prev) => prev ? { ...prev, has_embedding: false, images_used: null, generated_at: null } : null);
      setProgressMsg('');
    } catch (err) {
      setError('Error al eliminar: ' + err.message);
      setProgressMsg('');
    } finally {
      setVectorizing(false);
    }
  };

  const formatDate = (dt) => {
    if (!dt) return '—';
    return new Date(dt).toLocaleString('es-MX', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const handleLogout = async () => {
    await performLogout();
    navigate('/');
  };

  return (
    <div className="catalog-page">
      <header>
        <div className="logo">⚙️ Admin - FashionVision</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/inventory')}>Inventario</button>
          <button className="nav-active" onClick={() => {}}>Catálogo</button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
      </header>

      <main className="catalog-container">
        <h1 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>Catálogo Visual (CLIP)</h1>
        <p style={{ margin: '0 0 24px 0', color: '#64748b' }}>
          Vectoriza productos para detección por similitud visual sin reentrenar el modelo YOLO.
        </p>

        {error && <div className="catalog-error">{error}</div>}

        <div className="coverage-section">
          <div className="coverage-info">
            <span className="coverage-label">Cobertura del catálogo</span>
            <span className="coverage-count">
              {vectorizedCount} de {totalCount} productos vectorizados
            </span>
          </div>
          <div className="coverage-bar">
            <div className="coverage-fill" style={{ width: `${coveragePct}%` }} />
          </div>
        </div>

        {loading ? (
          <div className="catalog-loading">Cargando catálogo...</div>
        ) : (
          <div className="catalog-table-container">
            <table className="catalog-table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>SKU</th>
                  <th>Estado</th>
                  <th>Fecha vectorización</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {products.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="catalog-empty">
                      No hay productos activos en el catálogo.
                    </td>
                  </tr>
                ) : (
                  products.map((product) => (
                    <tr key={product.product_id}>
                      <td className="product-name-cell">{product.product_name}</td>
                      <td className="product-sku-cell">{product.product_name || '—'}</td>
                      <td>
                        <span className={`status-badge ${product.has_embedding ? 'badge-vect' : 'badge-novect'}`}>
                          {product.has_embedding ? 'Vectorizado' : 'Sin embedding'}
                        </span>
                      </td>
                      <td className="date-cell">{formatDate(product.generated_at)}</td>
                      <td>
                        <button className="action-btn" onClick={() => openDrawer(product)}>
                          {product.has_embedding ? 'Gestionar' : 'Vectorizar'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {drawerOpen && selectedProduct && (
        <div className="drawer-overlay" onClick={closeDrawer}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h2>Vectorizar Producto</h2>
              <button className="drawer-close" onClick={closeDrawer}>&times;</button>
            </div>

            <div className="drawer-body">
              <div className="drawer-product-info">
                <h3>{selectedProduct.product_name}</h3>
                <span className={`status-badge ${selectedProduct.has_embedding ? 'badge-vect' : 'badge-novect'}`}>
                  {selectedProduct.has_embedding ? 'Vectorizado' : 'Sin embedding'}
                </span>
                {selectedProduct.images_used && (
                  <p className="drawer-meta">
                    Imágenes usadas: {selectedProduct.images_used} &middot;{' '}
                    {formatDate(selectedProduct.generated_at)}
                  </p>
                )}
              </div>

              {progressMsg && (
                <div className="progress-bar-container">
                  <div className="progress-bar-indeterminate" />
                  <span className="progress-msg">{progressMsg}</span>
                </div>
              )}

              <div className="drawer-section">
                <h4>Vectorizar con imágenes existentes</h4>
                <p className="drawer-hint">
                  Usa las imágenes ya cargadas en Cloudinary para este producto.
                </p>
                <button
                  className="vect-btn"
                  onClick={() => handleVectorize(true)}
                  disabled={vectorizing}
                >
                  Vectorizar con imágenes existentes
                </button>
              </div>

              <div className="drawer-section">
                <h4>Subir fotos nuevas (máx 5)</h4>
                <p className="drawer-hint">Formatos: JPEG, PNG, WebP. Mínimo 1, máximo 5 fotos.</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  multiple
                  onChange={handleFileSelect}
                  disabled={vectorizing}
                  className="file-input"
                />
                {uploadFiles.length > 0 && (
                  <div className="file-list">
                    {uploadFiles.map((f, i) => (
                      <span key={i} className="file-chip">{f.name}</span>
                    ))}
                  </div>
                )}
                <button
                  className="vect-btn"
                  onClick={() => handleVectorize(false)}
                  disabled={vectorizing || uploadFiles.length === 0}
                >
                  Guardar y vectorizar
                </button>
              </div>

              {selectedProduct.has_embedding && (
                <div className="drawer-section drawer-danger">
                  <h4>Eliminar embedding</h4>
                  <p className="drawer-hint">
                    El producto dejará de ser detectable por cámara. Podrás volver a vectorizarlo después.
                  </p>
                  <button
                    className="vect-btn vect-btn-danger"
                    onClick={handleDeleteEmbedding}
                    disabled={vectorizing}
                  >
                    Eliminar embedding
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CatalogManager;
