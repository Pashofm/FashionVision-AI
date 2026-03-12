import React from 'react';

const InventoryTable = ({ productos }) => {
  if (!productos || productos.length === 0) return null;

  return (
    <div className="inventory-table">
      <h3>Inventario</h3>
      <table>
        <thead>
          <tr>
            <th>Imagen</th>
            <th>Nombre</th>
            <th>Color</th>
            <th>Tipo</th>
          </tr>
        </thead>
        <tbody>
          {productos.map((p) => (
            <tr key={p.id}>
              <td>
                {p.imagen && <img src={p.imagen} alt={p.nombre} className="table-image" />}
              </td>
              <td>{p.nombre}</td>
              <td>{p.color}</td>
              <td>{p.tipoPrenda}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default InventoryTable;
