const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export async function detectClothes(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);

  const response = await fetch(`${API_URL}/api/detect`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Detection failed: ${response.statusText}`);
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

export async function getProducts() {
  const response = await fetch(`${API_URL}/api/products`);
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.statusText}`);
  }
  return response.json();
}

export async function getProductByYoloClass(yoloClassName) {
  const response = await fetch(`${API_URL}/api/products/by-yolo/${yoloClassName}`);
  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch product: ${response.statusText}`);
  }
  return response.json();
}

export async function getCategories() {
  const response = await fetch(`${API_URL}/api/categories`);
  if (!response.ok) {
    throw new Error(`Failed to fetch categories: ${response.statusText}`);
  }
  return response.json();
}

export async function login(email, password) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error(`Login failed: ${response.statusText}`);
  }
  return response.json();
}

export async function uploadImage(file, folder = 'fashionvision/products') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('folder', folder);

  const response = await fetch(`${API_URL}/api/upload/image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteImage(publicId) {
  const response = await fetch(`${API_URL}/api/upload/image/${publicId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Delete failed: ${response.statusText}`);
  }

  return response.json();
}

// ==================== SESSION FUNCTIONS ====================

export async function createSession(stationId = 'client-kiosk', clientUserId = null) {
  const response = await fetch(`${API_URL}/api/sessions`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ station_id: stationId, client_user_id: clientUserId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }
  return response.json();
}

// ==================== CART FUNCTIONS ====================

export async function createCart(sessionId) {
  const response = await fetch(`${API_URL}/api/carts`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create cart: ${response.statusText}`);
  }
  return response.json();
}

export async function getCarts(status = null) {
  const url = status ? `${API_URL}/api/carts?status=${status}` : `${API_URL}/api/carts`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch carts: ${response.statusText}`);
  }
  return response.json();
}

export async function getCart(cartId) {
  const response = await fetch(`${API_URL}/api/carts/${cartId}`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch cart: ${response.statusText}`);
  }
  return response.json();
}

export async function getPendingCarts() {
  const response = await fetch(`${API_URL}/api/carts/admin`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch pending carts: ${response.statusText}`);
  }
  return response.json();
}

export async function addCartItem(cartId, item) {
  const response = await fetch(`${API_URL}/api/carts/${cartId}/items`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(item),
  });
  if (!response.ok) {
    throw new Error(`Failed to add item to cart: ${response.statusText}`);
  }
  return response.json();
}

export async function removeCartItem(cartId, itemId) {
  const response = await fetch(`${API_URL}/api/carts/${cartId}/items/${itemId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to remove item: ${response.statusText}`);
  }
  return response.json();
}

export async function updateCartStatus(cartId, status, notes = null) {
  const body = { status };
  if (notes !== null) body.notes = notes;
  const response = await fetch(`${API_URL}/api/carts/${cartId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Failed to update cart: ${response.statusText}`);
  }
  return response.json();
}

export async function submitCart(cartId) {
  return updateCartStatus(cartId, 'submitted');
}

export async function approveCart(cartId) {
  return updateCartStatus(cartId, 'processing');
}

export async function rejectCart(cartId, notes = null) {
  return updateCartStatus(cartId, 'cancelled', notes);
}

export async function markCartPaid(cartId) {
  return updateCartStatus(cartId, 'paid');
}
