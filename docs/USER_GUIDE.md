# Guía de Usuario

FashionVision AI tiene tres perfiles principales: administrador, cajero y cliente de kiosco. Esta guía describe el flujo funcional de la demo local.

## Antes de empezar

Levanta la aplicación siguiendo [QUICKSTART.md](../QUICKSTART.md) y abre `http://localhost`.

Usuarios incluidos en el seed de demostración:

| Perfil | Usuario | Contraseña | Función principal |
|---|---|---|---|
| Administrador | `admin@tienda.com` | `admin123` | Catálogo, inventario, caja y reportes |
| Cajero | `cajero@tienda.com` | `admin123` | Revisión de carritos y caja |
| Cliente | `cliente@demo.com` | `admin123` | Kiosco y carrito de compra |

Estas credenciales son únicamente para desarrollo y demostración. Cámbialas antes de cualquier uso real.

## Flujo del administrador

1. Inicia sesión con el usuario administrador.
2. Revisa el **Dashboard** para consultar ventas, productos destacados y alertas.
3. En **Catálogo**, crea categorías, productos y variantes de talla/color.
4. Añade imágenes de los productos si está configurado Cloudinary.
5. En **Inventario**, registra existencias, ubicaciones y movimientos de stock.
6. Genera embeddings de las imágenes del catálogo cuando quieras usar matching visual.
7. En **Reportes**, consulta ventas, productos más vendidos, tendencias y alertas.

Cada variante tiene su propio SKU y stock. Un producto sin variantes no debe considerarse listo para venderse desde el kiosco.

## Flujo del cliente en kiosco

1. Accede a la pantalla de cliente o inicia sesión con `cliente@demo.com`.
2. Permite el acceso a la cámara cuando el navegador lo solicite, o selecciona una imagen.
3. Captura una prenda procurando que esté bien iluminada y visible.
4. El sistema combina detección YOLO y matching CLIP para buscar coincidencias en el catálogo.
5. Revisa los productos detectados y sus variantes disponibles.
6. Añade los productos al carrito y ajusta las cantidades.
7. Envía el carrito para que lo revise el cajero.

La cámara funciona en `http://localhost`, que los navegadores tratan como un contexto seguro. La detección puede tardar más la primera vez mientras se prepara la caché de los modelos.

## Flujo del cajero

1. Cierra la sesión del cliente y entra con `cajero@tienda.com`.
2. Abre la sección **Caja**.
3. Selecciona un carrito enviado por un cliente.
4. Comprueba productos, variantes, cantidades, precios y disponibilidad.
5. Aprueba el carrito para iniciar el proceso de pago.
6. Usa el terminal de pago simulado para completar o cancelar la operación.
7. Genera o visualiza el recibo.

El terminal actual es un **mock**: simula estados de pago, pero no realiza cargos reales ni se conecta a hardware bancario.

## Recibos e inventario

Al completar una venta, el sistema crea la orden y el recibo, y actualiza las existencias según la variante vendida. La impresión real depende del driver configurado. Consulta [MODULO_IMPRESION_RECIBOS.md](MODULO_IMPRESION_RECIBOS.md) para integrar una impresora.

## Sesiones y cierre de sesión

- Las sesiones de administrador y cajero usan tokens JWT.
- El frontend renueva el refresh token mientras la sesión siga activa.
- El kiosco mantiene una sesión y un carrito para recuperar el trabajo tras una recarga.
- El cliente debe cerrar sesión al terminar para limpiar la sesión del kiosco.

Para conocer los estados internos de sesiones y carritos, consulta [SESIONES_Y_CARRITOS.md](SESIONES_Y_CARRITOS.md) y [modulo-sesion-logout.md](modulo-sesion-logout.md).

## Limitaciones de la demo

- El pago es simulado y no debe utilizarse para cobrar a clientes reales.
- Las cuentas y contraseñas del seed son públicas.
- La detección depende de la calidad del modelo y de que el producto esté registrado en el catálogo.
- Cloudinary es opcional; sin él, el almacenamiento remoto de imágenes no está disponible.
- La instalación local está pensada para desarrollo y demostración, no para exponerla directamente a Internet.
