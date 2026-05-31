const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL === '/' ? '' : BASE_URL;

const TOKEN_REFRESH_BUFFER_SECONDS = 60;

let isRefreshing = false;
let refreshSubscribers = [];

export const getHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback);
};

const onTokenRefreshed = (token) => {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
};

export async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${API_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    throw new Error('Token refresh failed');
  }

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data.access_token;
}

const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

const isTokenExpiringSoon = () => {
  const expiresIn = localStorage.getItem('expires_in');
  if (!expiresIn) return true;
  const expiryTime = parseInt(expiresIn, 10) * 1000;
  const bufferTime = TOKEN_REFRESH_BUFFER_SECONDS * 1000;
  return Date.now() >= (expiryTime - bufferTime);
};

const handleUnauthorized = async () => {
  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token) => {
        resolve(token);
      });
    });
  }

  isRefreshing = true;
  try {
    const newToken = await refreshAccessToken();
    onTokenRefreshed(newToken);
    return newToken;
  } catch (error) {
    onTokenRefreshed(null);
    throw error;
  } finally {
    isRefreshing = false;
  }
};

const authenticatedFetch = async (url, options = {}) => {
  let token = getAccessToken();

  if (!token || isTokenExpiringSoon()) {
    try {
      token = await handleUnauthorized();
    } catch (error) {
      window.location.href = '/';
      throw error;
    }
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    try {
      token = await handleUnauthorized();
      headers['Authorization'] = `Bearer ${token}`;
      return fetch(url, { ...options, headers });
    } catch (error) {
      window.location.href = '/';
      throw error;
    }
  }

  return response;
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

export async function getDetectionProductById(productId) {
  const response = await fetch(`${API_URL}/api/detect/product-by-id/${productId}`);
  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch detection product by id: ${response.statusText}`);
  }
  return response.json();
}

export async function searchProductVariant(productId, sizeAttributeId, colorAttributeId) {
  const params = new URLSearchParams();
  if (sizeAttributeId) params.append('size_attribute_id', sizeAttributeId);
  if (colorAttributeId) params.append('color_attribute_id', colorAttributeId);

  const response = await fetch(`${API_URL}/api/products/${productId}/variants/search?${params}`);
  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Error searching variant: ${response.statusText}`);
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
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('expires_in', data.expires_in.toString());
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
}

export async function refreshToken() {
  return refreshAccessToken();
}

export function getStoredUser() {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

export function isAuthenticated() {
  return !!localStorage.getItem('access_token');
}

export function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('expires_in');
  localStorage.removeItem('user');
}

export async function performLogout() {
  try {
    await authenticatedFetch(`${API_URL}/api/auth/logout`, { method: 'POST' });
  } catch (err) {
    console.warn('Server logout failed, clearing local state anyway:', err);
  }
  logout();
}

export async function extendSession() {
  const response = await authenticatedFetch(`${API_URL}/api/auth/session/extend`, {
    method: 'GET',
  });
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

export async function getOrCreateCartBySession(sessionId) {
  const response = await fetch(`${API_URL}/api/carts/by-session/${sessionId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to get/create cart: ${response.statusText}`);
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

export async function updateCartStatus(cartId, status, notes = null, paymentMethod = null) {
  const body = { status };
  if (notes !== null) body.notes = notes;
  if (paymentMethod !== null) body.payment_method = paymentMethod;
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

export async function processPayment(cartId, paymentMethod = 'cash') {
  const body = { status: 'paid', payment_method: paymentMethod };
  const response = await fetch(`${API_URL}/api/carts/${cartId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Failed to process payment: ${response.statusText}`);
  }
  return response.json();
}

// ==================== INVENTORY FUNCTIONS ====================

export async function getProductsWithStock(categoryId = null, search = null) {
  let url = `${API_URL}/api/products/stock/all`;
  const params = new URLSearchParams();
  if (categoryId) params.append('category_id', categoryId);
  if (search) params.append('search', search);
  if (params.toString()) url += `?${params.toString()}`;

  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.statusText}`);
  }
  return response.json();
}

export async function getLowStockProducts() {
  const response = await fetch(`${API_URL}/api/inventory/low-stock`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch low stock products: ${response.statusText}`);
  }
  return response.json();
}

export async function getInventoryMovements(variantId = null) {
  let url = `${API_URL}/api/inventory-movements`;
  if (variantId) url += `?product_variant_id=${variantId}`;

  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch inventory movements: ${response.statusText}`);
  }
  return response.json();
}

export async function adjustInventory(variantId, quantityChange, reason, referenceId = null) {
  const body = {
    quantity_change: quantityChange,
    reason: reason
  };
  if (referenceId) body.reference_id = referenceId;

  const response = await fetch(`${API_URL}/api/inventory/adjust?variant_id=${variantId}`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Failed to adjust inventory: ${response.statusText}`);
  }
  return response.json();
}

export async function restockInventory(variantId, quantity, notes = null, referenceId = null) {
  const body = {
    quantity: quantity,
    notes: notes
  };
  if (referenceId) body.reference_id = referenceId;

  const response = await fetch(`${API_URL}/api/inventory/restock?variant_id=${variantId}`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Failed to restock: ${response.statusText}`);
  }
  return response.json();
}

export async function updateStockThreshold(variantId, threshold) {
  const response = await fetch(`${API_URL}/api/inventory/${variantId}/threshold?threshold=${threshold}`, {
    method: 'PUT',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to update threshold: ${response.statusText}`);
  }
  return response.json();
}

// ==================== POS TERMINAL FUNCTIONS ====================

export async function posInitializePayment(cartId, amount, currency = 'MXN') {
  const response = await fetch(`${API_URL}/api/payments/pos/init`, {
    method: 'POST',
    headers: { ...getHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ cart_id: cartId, amount, currency }),
  });
  if (!response.ok) {
    throw new Error(`Failed to initialize POS payment: ${response.statusText}`);
  }
  return response.json();
}

export async function posWaitForCard(transactionId) {
  const response = await fetch(`${API_URL}/api/payments/pos/wait-card?transaction_id=${transactionId}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to wait for card: ${response.statusText}`);
  }
  return response.json();
}

export async function posProcessPayment(transactionId) {
  const response = await fetch(`${API_URL}/api/payments/pos/process?transaction_id=${transactionId}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to process payment: ${response.statusText}`);
  }
  return response.json();
}

export async function posCancelTransaction(transactionId) {
  const response = await fetch(`${API_URL}/api/payments/pos/cancel?transaction_id=${transactionId}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to cancel transaction: ${response.statusText}`);
  }
  return response.json();
}

export async function posGetStatus(transactionId) {
  const response = await fetch(`${API_URL}/api/payments/pos/status/${transactionId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to get transaction status: ${response.statusText}`);
  }
  return response.json();
}

export async function posCompletePayment(transactionId, cartId) {
  const response = await fetch(`${API_URL}/api/payments/pos/complete-payment?transaction_id=${transactionId}&cart_id=${cartId}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to complete payment: ${response.statusText}`);
  }
  return response.json();
}

// ==================== PRINTER DRIVER FUNCTIONS ====================

export async function getCurrentPrinterDriver() {
  const response = await authenticatedFetch(`${API_URL}/api/printers/driver`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Failed to get current printer driver: ${response.statusText}`);
  }
  return response.json();
}

export async function getAvailablePrinterDrivers() {
  const response = await authenticatedFetch(`${API_URL}/api/printers/drivers`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Failed to get available printer drivers: ${response.statusText}`);
  }
  return response.json();
}

export async function setPrinterDriver(driverType) {
  const response = await fetch(`${API_URL}/api/printers/driver?driver_type=${driverType}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to set printer driver: ${response.statusText}`);
  }
  return response.json();
}

export async function printReceipt(receiptId) {
  const response = await fetch(`${API_URL}/api/receipts/${receiptId}/print`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to print receipt: ${response.statusText}`);
  }
  return response.json();
}

export async function getReceiptPreview(receiptId) {
  const response = await fetch(`${API_URL}/api/receipts/${receiptId}/preview`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to get receipt preview: ${response.statusText}`);
  }
  return response.json();
}

// ==================== SUPPLIER FUNCTIONS ====================

export async function getSuppliers(isActive = null) {
  let url = `${API_URL}/api/suppliers`;
  if (isActive !== null) url += `?is_active=${isActive}`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch suppliers: ${response.statusText}`);
  }
  return response.json();
}

export async function createSupplier(supplierData) {
  const response = await fetch(`${API_URL}/api/suppliers`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(supplierData),
  });
  if (!response.ok) {
    throw new Error(`Failed to create supplier: ${response.statusText}`);
  }
  return response.json();
}

export async function updateSupplier(supplierId, supplierData) {
  const response = await fetch(`${API_URL}/api/suppliers/${supplierId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(supplierData),
  });
  if (!response.ok) {
    throw new Error(`Failed to update supplier: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteSupplier(supplierId) {
  const response = await fetch(`${API_URL}/api/suppliers/${supplierId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to delete supplier: ${response.statusText}`);
  }
  return response.json();
}

// ==================== ATTRIBUTE FUNCTIONS ====================

export async function getAttributes(type = null) {
  let url = `${API_URL}/api/attributes`;
  if (type) url += `?type=${type}`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch attributes: ${response.statusText}`);
  }
  return response.json();
}

export async function getAllAttributes(includeInactive = false) {
  let url = `${API_URL}/api/attributes?include_inactive=${includeInactive}`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch attributes: ${response.statusText}`);
  }
  return response.json();
}

export async function reactivateAttribute(attributeId) {
  const response = await fetch(`${API_URL}/api/attributes/${attributeId}/reactivate`, {
    method: 'PUT',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to reactivate attribute: ${response.statusText}`);
  }
  return response.json();
}

export async function createAttribute(attributeData) {
  const response = await fetch(`${API_URL}/api/attributes`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(attributeData),
  });
  if (!response.ok) {
    throw new Error(`Failed to create attribute: ${response.statusText}`);
  }
  return response.json();
}

export async function updateAttribute(attributeId, attributeData) {
  const response = await fetch(`${API_URL}/api/attributes/${attributeId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(attributeData),
  });
  if (!response.ok) {
    throw new Error(`Failed to update attribute: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteAttribute(attributeId) {
  const response = await fetch(`${API_URL}/api/attributes/${attributeId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to delete attribute: ${response.statusText}`);
  }
  return response.json();
}

export async function getAttributesWithStock(type = null, includeInactive = false) {
  let url = `${API_URL}/api/attributes/with-stock-status?include_inactive=${includeInactive}`;
  if (type) url += `&type=${type}`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch attributes with stock: ${response.statusText}`);
  }
  return response.json();
}

export async function getAttributeProducts(attributeId) {
  const response = await fetch(`${API_URL}/api/attributes/${attributeId}/products`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch attribute products: ${response.statusText}`);
  }
  return response.json();
}

// ==================== PRODUCT ATTRIBUTES ====================

export async function getProductAttributes(productId) {
  const response = await fetch(`${API_URL}/api/products/${productId}/attributes`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch product attributes: ${response.statusText}`);
  }
  return response.json();
}

export async function addProductAttributes(productId, attributeIds) {
  const response = await fetch(`${API_URL}/api/products/${productId}/attributes`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ attribute_ids: attributeIds }),
  });
  if (!response.ok) {
    throw new Error(`Failed to add product attributes: ${response.statusText}`);
  }
  return response.json();
}

export async function removeProductAttribute(productId, attributeId) {
  const response = await fetch(`${API_URL}/api/products/${productId}/attributes/${attributeId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to remove product attribute: ${response.statusText}`);
  }
  return response.json();
}

export async function getProductAttributesWithStock(productId) {
  const response = await fetch(`${API_URL}/api/products/${productId}/attributes-with-stock`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch product attributes with stock: ${response.statusText}`);
  }
  return response.json();
}

export async function getAvailableProductAttributes(productId) {
  const response = await fetch(`${API_URL}/api/products/${productId}/available-attributes`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch available product attributes: ${response.statusText}`);
  }
  return response.json();
}

export async function linkProductAttributes(productId, attributeIds) {
  const response = await fetch(`${API_URL}/api/products/${productId}/attributes/link`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ attribute_ids: attributeIds }),
  });
  if (!response.ok) {
    throw new Error(`Failed to link product attributes: ${response.statusText}`);
  }
  return response.json();
}

// ==================== PRICE FUNCTIONS ====================

export async function getPriceBreakdown(productId, variantId = null) {
  let url = `${API_URL}/api/products/${productId}/price-breakdown`;
  if (variantId) url += `?variant_id=${variantId}`;
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch price breakdown: ${response.statusText}`);
  }
  return response.json();
}

export async function getProductPriceHistory(productId, limit = 50) {
  const response = await fetch(`${API_URL}/api/products/${productId}/price-history?limit=${limit}`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch price history: ${response.statusText}`);
  }
  return response.json();
}

export async function updateProductPrices(productId, priceData) {
  const response = await fetch(`${API_URL}/api/products/${productId}/update-prices`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(priceData),
  });
  if (!response.ok) {
    throw new Error(`Failed to update product prices: ${response.statusText}`);
  }
  return response.json();
}

// ==================== INVENTORY STATUS FUNCTIONS ====================

export async function updateInventoryStatus(variantId, statusData) {
  const response = await fetch(`${API_URL}/api/inventory/${variantId}/status`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(statusData),
  });
  if (!response.ok) {
    throw new Error(`Failed to update inventory status: ${response.statusText}`);
  }
  return response.json();
}

export async function getInventoryByLocation(location) {
  const response = await fetch(`${API_URL}/api/inventory/warehouse/${encodeURIComponent(location)}`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch inventory by location: ${response.statusText}`);
  }
  return response.json();
}

export async function getInventoryByStatus(status) {
  const response = await fetch(`${API_URL}/api/inventory/by-status?status=${status}`, { headers: getHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to fetch inventory by status: ${response.statusText}`);
  }
  return response.json();
}
