/**
 * Servicio de Catálogo y Embeddings para FashionVision AI.
 *
 * @module services/catalogService
 * @description Maneja la generación y consulta de embeddings visuales (CLIP)
 *   para matching de productos en el catálogo desde el módulo de detección.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Consulta el estado del sistema de embeddings.
 * @returns {Promise<Object>} Estado actual (productos con/sin embedding, total)
 */
export async function getEmbeddingStatus() {
  const response = await fetch(`${API_URL}/api/catalog/embedding-status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch embedding status: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Genera un embedding visual para un producto usando CLIP.
 * Puede recibir archivos de imagen o usar las imágenes existentes del producto.
 * @param {string} productId - UUID del producto
 * @param {File[]} [files] - Archivos de imagen opcionales para generar el embedding
 * @returns {Promise<Object>} Resultado de la generación
 */
export async function generateEmbedding(productId, files) {
  if (files && files.length > 0) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const headers = {};
    const token = localStorage.getItem('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(
      `${API_URL}/api/products/${productId}/generate-embedding`,
      { method: 'POST', headers, body: formData }
    );
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Failed to generate embedding: ${response.statusText}`);
    }
    return response.json();
  }

  const response = await fetch(
    `${API_URL}/api/products/${productId}/generate-embedding`,
    { method: 'POST', headers: getAuthHeaders() }
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `Failed to generate embedding: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Elimina el embedding de un producto.
 * @param {string} productId - UUID del producto
 * @returns {Promise<Object>} Resultado de la eliminación
 */
export async function deleteEmbedding(productId) {
  const response = await fetch(
    `${API_URL}/api/products/${productId}/embedding`,
    { method: 'DELETE', headers: getAuthHeaders() }
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `Failed to delete embedding: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Busca productos similares en el catálogo usando CLIP.
 * Compara una imagen detectada con los embeddings de todos los productos.
 * @param {File} imageFile - Imagen de la prenda detectada
 * @param {number[]} bbox - Bounding box [x1, y1, x2, y2] de la detección
 * @returns {Promise<Object>} Resultados de matching (product_id, similarity)
 */
export async function matchCatalog(imageFile, bbox) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('bbox', JSON.stringify(bbox));

  const response = await fetch(`${API_URL}/api/detect/match-catalog`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `Failed to match catalog: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Obtiene un producto por ID para el módulo de detección.
 * @param {string} productId - UUID del producto
 * @returns {Promise<Object|null>} Producto o null si no existe
 */
export async function getDetectionProductById(productId) {
  const response = await fetch(`${API_URL}/api/detect/product-by-id/${productId}`);
  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch detection product: ${response.statusText}`);
  }
  return response.json();
}
