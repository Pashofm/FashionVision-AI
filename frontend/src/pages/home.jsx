import React, { useState } from 'react';
import '../styles/home.css';

const Home = () => {
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(false);

  const agregarConIA = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/test-detection');
      const result = await response.json();
      setProducto(result.data);
    } catch (error) {
      console.error("Error conectando con el backend:", error);
      alert("Error: Asegúrate de que FastAPI esté corriendo en el puerto 8000");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <header>
        <div className="logo">FashionVision IA</div>
        <nav>
          <button>Dashboard</button>
          <button>Pago</button>
          <button>Inventario</button>
        </nav>
      </header>

      <main className="container">
        <section className="button-section">
          <button className="add-btn" onClick={agregarConIA} disabled={loading}>
            {loading ? "Procesando..." : "Agregar producto"}
          </button>
        </section>

        <section className="inventory">
          {!producto ? (
            <p>No se encuentran productos en el inventario</p>
          ) : (
            <div className="product-card">
              <h3>✨ Análisis de Prenda</h3>
              <hr style={{ border: '0.5px solid #eee', marginBottom: '15px' }} />
              <p><strong>Categoría:</strong> {producto.prenda}</p>
              <p><strong>Color predominante:</strong> {producto.color}</p>
              <p><strong>Confianza:</strong> {(producto.confianza * 100).toFixed(0)}%</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Home;
