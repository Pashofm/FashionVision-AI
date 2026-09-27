/**
 * Hook de gestión de productos en pestañas para el módulo Kiosko.
 *
 * @module hooks/useProductTabs
 * @description Maneja el estado de los productos detectados por el kiosko:
 *   - Máximo 5 productos simultáneos (MAX_PRODUCTS)
 *   - Navegación por pestañas (índice activo)
 *   - Selección de talla y color por producto
 *   - Matching de variantes disponibles
 *   - Valores por defecto según tipo de prenda
 *
 * @returns {Object} Estado de productos y funciones de manipulación
 */

import { useState, useCallback, useMemo } from 'react';

const MAX_PRODUCTS = 5;

const generateId = () => `prod_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const getDefaultSizes = (yoloClassName) => {
  const sizeMap = {
    'accessories': ['One Size'],
    'clothing': ['S', 'M', 'L', 'XL'],
    'shoes': ['25', '26', '27', '28', '29'],
    'bags': ['One Size']
  };
  return sizeMap[yoloClassName?.toLowerCase()] || ['S', 'M', 'L', 'XL'];
};

const getDefaultColors = (yoloClassName) => {
  const colorMap = {
    'accessories': ['Unico'],
    'clothing': ['Blanco', 'Negro', 'Azul'],
    'shoes': ['Negro', 'Blanco', 'Marrón'],
    'bags': ['Unico']
  };
  return colorMap[yoloClassName?.toLowerCase()] || ['Unico'];
};

const useProductTabs = () => {
  const [products, setProducts] = useState([]);
  const [activeTabIndex, setActiveTabIndex] = useState(-1);

  const activeProduct = useMemo(() => {
    if (activeTabIndex >= 0 && activeTabIndex < products.length) {
      return products[activeTabIndex];
    }
    return null;
  }, [products, activeTabIndex]);

  /**
   * Agrega un producto detectado. Si ya existe uno similar (mismo ID y bbox cercano),
   * lo actualiza en lugar de duplicarlo.
   * @param {Object} productData — Datos del producto detectado
   * @returns {{ success: boolean, index?: number, isUpdate?: boolean, message?: string }}
   */
  const addProduct = useCallback((productData) => {
    if (products.length >= MAX_PRODUCTS) {
      return { success: false, message: `Máximo ${MAX_PRODUCTS} productos` };
    }

    const existingIndex = products.findIndex(
      p => p.product_id === productData.product_id && productData.product_id &&
           Math.abs(p.bbox[0] - productData.bbox[0]) < 50 &&
           Math.abs(p.bbox[1] - productData.bbox[1]) < 50
    );

    if (existingIndex !== -1) {
      setProducts(prev => prev.map((p, i) =>
        i === existingIndex ? { ...p, ...productData } : p
      ));
      setActiveTabIndex(existingIndex);
      const existingProduct = products[existingIndex];
      return { success: true, index: existingIndex, isUpdate: true, productId: existingProduct?.id };
    }

    const newProduct = {
      id: generateId(),
      name: productData.name || productData.class || 'Producto',
      tipoProducto: productData.tipoProducto || productData.name || 'Prenda',
      marca: productData.brand || 'FashionCo',
      precio: productData.price || 0,
      sku: productData.sku || 'N/A',
      colors: productData.colors || getDefaultColors(productData.name).map(c => ({ name: c, hex: null, stock: 0 })),
      sizes: productData.sizes || getDefaultSizes(productData.name).map(s => ({ name: s, stock: 0 })),
      confidence: productData.confidence || 0,
      bbox: productData.bbox || [0, 0, 0, 0],
      selectedSize: null,
      selectedColor: null,
      matchingVariant: null,
      selectionError: '',
      product_id: productData.product_id || null,
      imageData: productData.imageData || null,
      matchSource: productData.matchSource || 'none',
      matchSimilarity: productData.matchSimilarity || null,
      catalog_match: productData.catalog_match || null
    };

    const newIndex = products.length;
    setProducts(prev => [...prev, newProduct]);
    setActiveTabIndex(newIndex);

    return { success: true, index: newIndex, isUpdate: false, productId: newProduct.id };
  }, [products]);

  const removeProduct = useCallback((productId) => {
    setProducts(prev => {
      const newProducts = prev.filter(p => p.id !== productId);

      setActiveTabIndex(currentIndex => {
        if (newProducts.length === 0) {
          return -1;
        }
        if (currentIndex >= newProducts.length) {
          return Math.max(0, newProducts.length - 1);
        }
        return currentIndex;
      });

      return newProducts;
    });
  }, []);

  const setActiveTab = useCallback((index) => {
    if (index >= 0 && index < products.length) {
      setActiveTabIndex(index);
    }
  }, [products.length]);

  const updateProductVariant = useCallback((productId, variantData) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return { ...p, ...variantData };
      }
      return p;
    }));
  }, []);

  const updateProductImage = useCallback((productId, imageData) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return { ...p, imageData };
      }
      return p;
    }));
  }, []);

  const selectSize = useCallback((productId, size) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return {
          ...p,
          selectedSize: size,
          selectionError: p.selectedColor ? '' : p.selectionError
        };
      }
      return p;
    }));
  }, []);

  const selectColor = useCallback((productId, color) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return {
          ...p,
          selectedColor: color,
          selectionError: p.selectedSize ? '' : p.selectionError
        };
      }
      return p;
    }));
  }, []);

  const setMatchingVariant = useCallback((productId, variant) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return {
          ...p,
          matchingVariant: variant,
          selectionError: variant ? '' : 'Esta combinación no está disponible'
        };
      }
      return p;
    }));
  }, []);

  /**
   * Verifica si un producto tiene talla, color y variante seleccionados y hay stock.
   * @param {string} productId
   * @returns {boolean}
   */
  const canAddToCart = useCallback((productId) => {
    const product = products.find(p => p.id === productId);
    return product &&
           product.selectedSize &&
           product.selectedColor &&
           product.matchingVariant &&
           product.matchingVariant.quantity_available > 0;
  }, [products]);

  const getProductById = useCallback((productId) => {
    return products.find(p => p.id === productId) || null;
  }, [products]);

  const resetProduct = useCallback((productId) => {
    setProducts(prev => prev.map(p => {
      if (p.id === productId) {
        return {
          ...p,
          selectedSize: null,
          selectedColor: null,
          matchingVariant: null,
          selectionError: ''
        };
      }
      return p;
    }));
  }, []);

  const clearAllProducts = useCallback(() => {
    setProducts([]);
    setActiveTabIndex(-1);
  }, []);

  return {
    products,
    activeTabIndex,
    activeProduct,
    addProduct,
    removeProduct,
    setActiveTab,
    updateProductVariant,
    updateProductImage,
    selectSize,
    selectColor,
    setMatchingVariant,
    canAddToCart,
    getProductById,
    resetProduct,
    clearAllProducts,
    productCount: products.length,
    maxProducts: MAX_PRODUCTS
  };
};

export default useProductTabs;
