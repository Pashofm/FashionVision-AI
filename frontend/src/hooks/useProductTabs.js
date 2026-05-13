import { useState, useCallback, useMemo } from 'react';

const MAX_PRODUCTS = 5;

const generateId = () => `prod_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const traducirCategoria = (className) => {
  if (!className) return 'Prenda';
  const productoMap = {
    'gorra-roja-lacoste': 'Gorra',
    'top': 'Camiseta',
    'pants': 'Pantalón'
  };
  return productoMap[className.toLowerCase()] || className;
};

const getDefaultSizes = (yoloClassName) => {
  const sizeMap = {
    'gorra-roja-lacoste': ['One Size'],
    'top': ['S', 'M', 'L', 'XL'],
    'pants': ['28', '30', '32', '34', '36']
  };
  return sizeMap[yoloClassName?.toLowerCase()] || ['S', 'M', 'L', 'XL'];
};

const getDefaultColors = (yoloClassName) => {
  const colorMap = {
    'gorra-roja-lacoste': ['Rojo'],
    'top': ['Blanco', 'Negro', 'Azul'],
    'pants': ['Azul Marino', 'Negro', 'Gris']
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

  const addProduct = useCallback((productData) => {
    if (products.length >= MAX_PRODUCTS) {
      return { success: false, message: `Máximo ${MAX_PRODUCTS} productos` };
    }

    const existingIndex = products.findIndex(
      p => p.yolo_class_name === productData.yolo_class_name &&
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
      tipoProducto: traducirCategoria(productData.yolo_class_name),
      marca: productData.brand || 'FashionCo',
      precio: productData.price || 0,
      sku: productData.sku || 'N/A',
      colors: productData.colors || getDefaultColors(productData.yolo_class_name).map(c => ({ name: c, hex: null, stock: 0 })),
      sizes: productData.sizes || getDefaultSizes(productData.yolo_class_name).map(s => ({ name: s, stock: 0 })),
      yolo_class_name: productData.yolo_class_name || '',
      confidence: productData.confidence || 0,
      bbox: productData.bbox || [0, 0, 0, 0],
      selectedSize: null,
      selectedColor: null,
      matchingVariant: null,
      selectionError: '',
      product_id: productData.product_id || null,
      imageData: productData.imageData || null
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