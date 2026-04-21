import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts, getCategories } from '../services/api';

const Inventory = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role !== 'admin') {
      navigate('/');
      return;
    }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [productsData, categoriesData] = await Promise.all([
        getProducts(),
        getCategories()
      ]);
      setProducts(productsData);
      setCategories(categoriesData);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(filter.toLowerCase()) ||
    p.sku?.toLowerCase().includes(filter.toLowerCase())
  );

  const getCategoryName = (categoryId) => {
    const cat = categories.find(c => c.id === categoryId);
    return cat?.name || 'Sin categoría';
  };

  return (
    <div className="inventory-page">
      <header>
        <div className="logo">📦 Inventario - FashionVision</div>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button className="nav-active">Inventario</button>
        </nav>
      </header>

      <main className="container">
        <div className="section-header">
          <h2>📦 Gestión de Inventario</h2>
          <button className="btn-primary" onClick={fetchData}>
            🔄 Actualizar
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="search-bar">
          <input
            type="text"
            placeholder="Buscar producto por nombre o SKU..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="search-input"
          />
        </div>

        {loading ? (
          <div className="loading">Cargando productos...</div>
        ) : filteredProducts.length === 0 ? (
          <div className="no-data">
            <h3>No hay productos</h3>
            <p>Los productos aparecerán aquí cuando se agreguen</p>
          </div>
        ) : (
          <div className="products-table">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Nombre</th>
                  <th>Categoría</th>
                  <th>Precio</th>
                  <th>YOLO</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product) => (
                  <tr key={product.id}>
                    <td className="sku">{product.sku || '-'}</td>
                    <td className="name">{product.name}</td>
                    <td>{getCategoryName(product.category_id)}</td>
                    <td className="price">${parseFloat(product.price).toFixed(2)}</td>
                    <td className="yolo-tag">{product.yolo_class_name || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      <style>{`
        .inventory-page {
          min-height: 100vh;
          background: #f8fafc;
        }
        .search-bar {
          margin-bottom: 20px;
        }
        .search-input {
          width: 100%;
          padding: 12px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 14px;
        }
        .search-input:focus {
          outline: none;
          border-color: #667eea;
        }
        .products-table {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th {
          background: #f8fafc;
          padding: 12px 16px;
          text-align: left;
          font-weight: 600;
          color: #64748b;
          font-size: 12px;
          text-transform: uppercase;
        }
        td {
          padding: 12px 16px;
          border-top: 1px solid #e2e8f0;
        }
        .sku {
          font-family: monospace;
          color: #667eea;
        }
        .name {
          font-weight: 500;
          color: #1e293b;
        }
        .price {
          color: #11998e;
          font-weight: 600;
        }
        .yolo-tag {
          font-size: 12px;
          background: #f1f5f9;
          padding: 4px 8px;
          border-radius: 4px;
          color: #64748b;
        }
        .loading, .no-data {
          text-align: center;
          padding: 60px 20px;
          color: #64748b;
        }
        .nav-active {
          background: #667eea !important;
          color: white !important;
        }
      `}</style>
    </div>
  );
};

export default Inventory;
