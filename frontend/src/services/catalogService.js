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

export async function getEmbeddingStatus() {
  const response = await fetch(`${API_URL}/api/catalog/embedding-status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch embedding status: ${response.statusText}`);
  }
  return response.json();
}

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
