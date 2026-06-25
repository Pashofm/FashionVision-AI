# Changelog

Todas las cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2025

### Added

#### Sistema de Visión por Computadora
- Pipeline de detección YOLO + CLIP para reconocimiento de prendas
- Sistema de matching visual con CLIP para catálogo de productos
- Detección automática de prendas para cliente kiosko
- Tabla `product_embeddings` con soporte pgvector

#### Módulo de Inventario
- Gestión completa de inventario con variantes (talla, color)
- Umbrales de stock bajo personalizables por producto
- Alertas de inventario (stock bajo / agotado)
- Historial de movimientos de inventario
- Gestión de proveedores
- Reservas de stock por carrito

#### Módulo de Cliente (Kiosko)
- Pantalla de inicio con detección automática
- Sidebar izquierdo con revisión de productos
- Interfaz táctil optimizada
- Recuperación de carrito en localStorage

#### Módulo de Sesiones y Autenticación
- Arquitectura de sesión dual (auth + kiosk)
- Roles de usuario: admin, cashier, client
- Timeout de inactividad para kiosko (2 min + cuenta regresiva)
- Invalidación de tokens vía `last_logout_at`
- Login con ruteo basado en roles

#### Dashboard y Reportes
- Dashboard con auto-refresh cada 5 minutos
- Métricas: ticket promedio, métodos de pago, tendencia de ventas
- Reportes avanzados con filtros por período (hoy, semana, mes, personalizado)
- Comparativa entre períodos
- Exportación a CSV, PDF y Excel
- Gráficos de ventas por hora y por categoría

#### Módulo de Impresión de Recibos
- Patrón Strategy/Plugin con 4 drivers intercambiables
- Mock (desarrollo), TextFile, HTML, ESCPOS (térmicas)
- Integración con flujo de cajero

#### Módulo de Punto de Venta (POS)
- Integración con terminal POS (mock para desarrollo)
- Flujo completo: init → wait-card → process → confirm
- Diseño preparado para migración a Stripe Terminal

#### Infraestructura
- Entorno Docker completo con hot-reload para desarrollo
- Docker Compose con PostgreSQL 16 + pgvector + pgAdmin
- Migraciones Alembic con datos seed
- Scripts de automatización (setup, dev-start, dev-stop, deploy)
- Soporte multi-OS (Linux, macOS, Windows WSL2)

#### Testing
- 104+ tests (unitarios + integración)
- 7 módulos cubiertos: sessions, inventory, cart, client flow, detection, session API, inventory API
- Sistema de factories para generación de datos de prueba
- 19 fixtures documentados
- Scripts de setup/teardown de BD de testing

#### Documentación
- README completo con diagramas de arquitectura
- Guías de instalación multi-OS
- Documentación detallada de módulos (sesiones, POS, recibos)
- Guía de testing con referencia rápida y troubleshooting
- Comandos de referencia (695 líneas)
- Guía de pgAdmin (493 líneas)
