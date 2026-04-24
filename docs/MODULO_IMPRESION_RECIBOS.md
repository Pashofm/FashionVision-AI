# Módulo de Impresión de Recibos

## Resumen

Este documento describe el módulo de impresión de recibos de FashionVision AI, un sistema flexible y extensible que permite imprimir recibos usando diferentes drivers intercambiables.

## Arquitectura del Sistema

El módulo está diseñado con un patrón de **Strategy/Plugin** que permite:

- **Intercambiar drivers** sin modificar el código de la aplicación
- **Agregar nuevos drivers** sin modificar el código existente
- **Testing fácil** usando el driver Mock
- **Múltiples outputs** simultáneos si es necesario

### Estructura del Proyecto

```
backend/
├── app/services/printers/
│   ├── __init__.py              # Exports públicos
│   ├── driver_type.py           # Enum DriverType
│   ├── print_result.py          # Dataclass PrintResult
│   ├── base_driver.py           # Interfaz abstracta PrinterDriver
│   ├── receipt_printer_service.py  # Servicio singleton
│   └── drivers/
│       ├── __init__.py
│       ├── mock_printer_driver.py      # Para unit tests
│       ├── textfile_printer_driver.py  # Para auditoría
│       ├── html_printer_driver.py      # Para preview/email
│       └── escpos_printer_driver.py    # Para impresoras térmicas
├── receipts/
│   ├── audit/                   # Archivos de auditoría (TextFileDriver)
│   └── previews/                # HTML receipts (HTMLDriver)
└── tests/
    └── test_receipt_printer.py  # Tests unitarios
```

## Drivers Disponibles

### 1. MockPrinterDriver

**Uso:** Pruebas unitarias y desarrollo sin hardware.

**Características:**
- Almacena recibos en memoria
- Siempre retorna éxito
- Útil para tests automatizados

```python
from backend.app.services.printers import ReceiptPrinterService, DriverType

ReceiptPrinterService.set_driver(DriverType.MOCK)
result = await ReceiptPrinterService.print_receipt(receipt_data)
```

### 2. TextFilePrinterDriver

**Uso:** Auditoría y archivos de texto para compliance.

**Características:**
- Genera archivos `.txt` en `receipts/audit/`
- Formato plano legible
- Incluye timestamp en contenido

**Archivo generado:** `receipts/audit/REC-{receipt_number}-{timestamp}.txt`

```python
ReceiptPrinterService.set_driver(DriverType.TEXTFILE)
result = await ReceiptPrinterService.print_receipt(receipt_data)
# output_path: receipts/audit/REC-ABC12345-20240115_143022.txt
```

### 3. HTMLPrinterDriver

**Uso:** Vista previa en navegador o envío por email.

**Características:**
- Genera archivos `.html` completos
- Estilos CSS profesionales
- Listo para embedding en emails

**Archivo generado:** `receipts/previews/REC-{receipt_number}-{timestamp}.html`

```python
ReceiptPrinterService.set_driver(DriverType.HTML)
result = await ReceiptPrinterService.print_receipt(receipt_data)

# Para obtener el HTML directamente
html = await ReceiptPrinterService.preview_receipt(receipt_data)
```

### 4. ESCPOSPrinterDriver

**Uso:** Impresoras térmicas reales (Epson TM-T88, etc.)

**Características:**
- Envía comandos ESC/POS via Serial USB
- Soporta corte de papel
- Texto formateado para impresoras de 80mm

**Conexión:** USB Serial (pyserial)

```python
driver = ESCPOSPrinterDriver(port="/dev/ttyUSB0", baudrate=9600)
ReceiptPrinterService.set_driver(DriverType.ESCPOS)
result = await ReceiptPrinterService.print_receipt(receipt_data)
```

**Requerimiento:** `pip install pyserial`

## Intercambio de Drivers

### Cambio Global (Uso Normal)

El driver se configura globalmente y se mantiene hasta el próximo cambio:

```python
from backend.app.services.printers import ReceiptPrinterService, DriverType

# Cambiar a driver de auditoría
ReceiptPrinterService.set_driver(DriverType.TEXTFILE)

# Imprimir (usará textfile)
result = await ReceiptPrinterService.print_receipt(receipt_data)

# Cambiar a printer térmica para producción
ReceiptPrinterService.set_driver(DriverType.ESCPOS)

# Siguiente impresión usará ESCPOS
result = await ReceiptPrinterService.print_receipt(receipt_data)
```

### Verificar Driver Actual

```python
driver_type, driver_name = ReceiptPrinterService.get_current_driver()
print(f"Driver activo: {driver_name} ({driver_type.value})")
```

### Listar Drivers Disponibles

```python
drivers = ReceiptPrinterService.get_available_drivers()
for dt, name in drivers:
    print(f"{dt.value}: {name}")
```

## API Endpoints

### GET /api/printers/drivers

Lista todos los drivers disponibles.

```bash
curl -X GET http://localhost:8000/api/printers/drivers
```

**Response:**
```json
{
  "drivers": [
    {"type": "mock", "name": "Mock Printer Driver (Testing)"},
    {"type": "textfile", "name": "Text File Printer Driver (Audit)"},
    {"type": "html", "name": "HTML Printer Driver (Preview/Email)"},
    {"type": "escpos", "name": "ESCPOS Thermal Printer (/dev/ttyUSB0)"}
  ]
}
```

### GET /api/printers/driver

Obtiene el driver activo actualmente.

```bash
curl -X GET http://localhost:8000/api/printers/driver
```

**Response:**
```json
{
  "type": "mock",
  "name": "Mock Printer Driver (Testing)"
}
```

### POST /api/printers/driver

Cambia el driver activo.

```bash
curl -X POST "http://localhost:8000/api/printers/driver?driver_type=html"
```

**Response:**
```json
{
  "message": "Printer driver changed to html",
  "active_driver": "HTML Printer Driver (Preview/Email)"
}
```

### POST /api/receipts/{receipt_id}/print

Imprime un recibo existente usando el driver activo.

```bash
curl -X POST http://localhost:8000/api/receipts/{uuid}/print \
  -H "Authorization: Bearer {token}"
```

**Response:**
```json
{
  "success": true,
  "message": "HTML receipt generated: REC-ABC123-20240115.html",
  "driver_type": "html",
  "output_path": "receipts/previews/REC-ABC123-20240115.html",
  "print_duration_ms": 12,
  "printed_at": "2024-01-15T14:30:22.123456"
}
```

### GET /api/receipts/{receipt_id}/preview

Genera vista previa HTML de un recibo.

```bash
curl -X GET http://localhost:8000/api/receipts/{uuid}/preview
```

**Response:**
```json
{
  "html": "<!DOCTYPE html><html>...</html>"
}
```

## Uso Programático

### PrintReceipt con Datos Completos

```python
from backend.app.services.printers import ReceiptPrinterService, DriverType
from datetime import datetime

receipt_data = {
    "receipt_number": "REC-20240115-ABC123",
    "order_number": "ORD-20240115-00001",
    "items": [
        {"name": "Camiseta Algodon", "quantity": 2, "price": 299.99, "subtotal": 599.98},
        {"name": "Jean Slim Fit", "quantity": 1, "price": 599.99, "subtotal": 599.99}
    ],
    "subtotal": 1199.97,
    "tax_amount": 191.99,
    "total_amount": 1391.96,
    "payment_method": "card",
    "card_last_four": "4242",
    "authorization_code": "AUTH-123456",
    "cashier": "Maria Garcia",
    "created_at": datetime.utcnow().isoformat()
}

ReceiptPrinterService.set_driver(DriverType.HTML)
result = await ReceiptPrinterService.print_receipt(receipt_data)

if result.success:
    print(f"Receipt saved to: {result.output_path}")
else:
    print(f"Error: {result.message}")
```

### Validación Automática

El `PrinterDriver` base valida automáticamente que los campos requeridos estén presentes:

```python
required_fields = [
    "receipt_number", "order_number", "items",
    "subtotal", "tax_amount", "total_amount",
    "payment_method", "cashier", "created_at"
]
```

Si falta algún campo, se lanza `ValueError`.

### Preview Sin Imprimir

Para generar HTML sin escribir archivo:

```python
html = await ReceiptPrinterService.preview_receipt(receipt_data)
# Retorna HTML listo para mostrar/enviar
```

## Flujo de Intercambio de Drivers

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION START                            │
│                                                                 │
│    ReceiptPrinterService._current_driver = MockPrinterDriver    │
│                          (default)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│   Production Environment                                        │
│                                                                 │
│   POST /api/printers/driver {"driver_type": "textfile"}        │
│   → ReceiptPrinterService.set_driver(TEXTFILE)                  │
│   → _current_driver = TextFilePrinterDriver                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│   Receipt Created (after payment)                              │
│                                                                 │
│   POST /api/receipts/{id}/print                                 │
│   → ReceiptPrinterService.print_receipt(receipt_data)           │
│   → TextFilePrinterDriver.print(receipt_data)                  │
│   → File created: receipts/audit/REC-XXX.txt                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│   Hardware Setup Complete                                       │
│                                                                 │
│   POST /api/printers/driver {"driver_type": "escpos"}          │
│   → ReceiptPrinterService.set_driver(ESCPOS)                    │
│   → _current_driver = ESCPOSPrinterDriver                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│   Next Print Goes to Thermal Printer                            │
│                                                                 │
│   POST /api/receipts/{id}/print                                 │
│   → ReceiptPrinterService.print_receipt(receipt_data)           │
│   → ESCPOSPrinterDriver.print(receipt_data)                     │
│   → Bytes sent via Serial to printer                           │
│   → Paper cuts automatically                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Testing

### Ejecutar Tests

```bash
cd backend
source venv/bin/activate
SKIP_DB_TESTS=true python -m pytest tests/test_receipt_printer.py -v
```

### Tests con MockPrinterDriver

El `MockPrinterDriver` permite tests sin efectos secundarios:

```python
@pytest.mark.asyncio
async def test_print_accumulates_in_memory(self):
    driver = MockPrinterDriver()

    await driver.print(sample_receipt)
    await driver.print(sample_receipt)

    assert driver.get_print_count() == 2
    assert driver.get_prints()[0]["receipt_number"] == sample_receipt["receipt_number"]
```

### Test de Intercambiabilidad

```python
@pytest.mark.asyncio
async def test_all_drivers_work(self, sample_receipt_data):
    for driver_type in DriverType:
        ReceiptPrinterService.set_driver(driver_type)
        result = await ReceiptPrinterService.print_receipt(sample_receipt_data)

        # Todos deben retornar success (excepto ESCPOS si no hay hw)
        assert result.success or result.error_code == "ESCPOS_ERROR"
```

## Campos Requeridos del Receipt Data

```python
{
    "receipt_number": str,      # Identificador único del recibo
    "order_number": str,         # Número de orden asociada
    "items": [                  # Lista de items comprados
        {
            "name": str,        # Nombre del producto
            "quantity": int,    # Cantidad
            "price": float,     # Precio unitario
            "subtotal": float   # Subtotal (qty * price)
        }
    ],
    "subtotal": float,          # Subtotal antes de impuestos
    "tax_amount": float,        # Monto de impuesto
    "total_amount": float,      # Total final
    "payment_method": str,     # "cash" o "card"
    "cashier": str,            # Nombre del cajero
    "created_at": str          # ISO timestamp
}
```

## Campos Opcionales

```python
{
    # Para pagos con tarjeta
    "card_last_four": str,         # Últimos 4 dígitos
    "authorization_code": str,      # Código de autorización

    # Para otros métodos
    "cash_received": float,         # Efectivo recibido
    "change_given": float,          # Cambio devuelto
}
```

## Configuración de Producción

### Variables de Entorno (opcional)

```env
# Para ESCPOS
ESCPOS_PORT=/dev/ttyUSB0
ESCPOS_BAUD=9600

# Para TextFile audit
AUDIT_DIR=receipts/audit

# Para HTML output
HTML_OUTPUT_DIR=receipts/previews
```

### Dependencias

```bash
# Para ESCPOS (impresora térmica real)
pip install pyserial>=3.5

# Para testing
pip install pytest pytest-asyncio
```

## Checklist de Implementación

- [x] Estructura del módulo creada
- [x] Interfaz base PrinterDriver definida
- [x] MockPrinterDriver implementado (tests)
- [x] TextFilePrinterDriver implementado (auditoría)
- [x] HTMLPrinterDriver implementado (preview/email)
- [x] ESCPOSPrinterDriver implementado (thermal)
- [x] ReceiptPrinterService como singleton
- [x] Endpoints API agregados
- [x] Tests unitarios creados
- [x] Documentación completada

## Integración Frontend - Cashier

### Flujo de Confirmación de Pago

El frontend del Cashier detecta automáticamente el driver configurado y actúa según el tipo:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONFIRMAR PAGO                              │
│                                                                     │
│  1. processPayment() / posCompletePayment()                       │
│     └── Crea receipt en DB                                        │
│                                                                     │
│  2. getCurrentPrinterDriver() → {type, name}                      │
│                                                                     │
│     ┌──────────────┬──────────────┬──────────────┬─────────────┐ │
│     │ MOCK         │ TEXTFILE     │ HTML         │ ESCPOS     │ │
│     └──────┬───────┴──────┬───────┴──────┬───────┴──────┬─────┘ │
│            │              │              │              │       │
│            ▼              ▼              ▼              ▼       │
│     ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐   │
│     │Solo modal  │ │Print to    │ │Open new    │ │Print to  │   │
│     │(no action) │ │file        │ │tab with    │ │thermal   │   │
│     │            │ │silently    │ │HTML preview│ │printer   │   │
│     └────────────┘ └────────────┘ └────────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Configuración de Impresora en Cashier

El Cashier tiene un panel colapsable de configuración de impresora:

```
┌────────────────────────────────────────────────────────────┐
│ ▶ ⚙️ Configuración de Impresora [HTML]                      │
└────────────────────────────────────────────────────────────┘
```

Al expandir:
```
┌────────────────────────────────────────────────────────────┐
│ 🎛️ Driver de Impresora                                      │
│ Selecciona el método de salida para los recibos              │
│                                                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│ │   🧪    │ │   📄    │ │   🌐    │ │   🖨️   │            │
│ │  MOCK   │ │TEXTFILE │ │   HTML  │ │  ESCPOS │            │
│ │ (Test)  │ │ (Audit) │ │(Preview)│ │(Thermal │            │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                             │
│ Driver activo: HTML Printer Driver (Preview/Email)         │
└────────────────────────────────────────────────────────────┘
```

### Comportamiento por Driver

| Driver | Al confirmar pago | Resultado |
|--------|-------------------|-----------|
| **MOCK** | No hace nada especial | Muestra modal del recibo |
| **TEXTFILE** | Imprime a archivo | Toast "Guardado en auditoría" |
| **HTML** | Abre nueva pestaña | Preview HTML del recibo |
| **ESCPOS** | Envía a impresora | Toast "Impreso" |

### APIs Frontend (api.js)

```javascript
// Obtener driver activo
export async function getCurrentPrinterDriver() {
  const response = await authenticatedFetch(`${API_URL}/api/printers/driver`);
  return response.json();
}

// Obtener drivers disponibles
export async function getAvailablePrinterDrivers() {
  const response = await authenticatedFetch(`${API_URL}/api/printers/drivers`);
  return response.json();
}

// Cambiar driver
export async function setPrinterDriver(driverType) {
  const response = await fetch(`${API_URL}/api/printers/driver?driver_type=${driverType}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return response.json();
}

// Imprimir recibo
export async function printReceipt(receiptId) {
  const response = await fetch(`${API_URL}/api/receipts/${receiptId}/print`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return response.json();
}

// Obtener preview HTML
export async function getReceiptPreview(receiptId) {
  const response = await fetch(`${API_URL}/api/receipts/${receiptId}/preview`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return response.json();
}
```

### Persistencia del Driver

El driver seleccionado se mantiene a nivel de **sesión del servidor** (no localStorage). Esto significa:

- **Ventaja:** Consistencia entre pestañas y recargas
- **Consideración:** Si el servidor se reinicia, vuelve al default (MOCK)

Para persistir en el frontend, se puede guardar en localStorage y sincronizar al cargar:

```javascript
// Al cargar Cashier
const savedDriver = localStorage.getItem('printer_driver');
if (savedDriver) {
  try {
    await setPrinterDriver(savedDriver);
  } catch (e) {
    console.warn('Failed to restore printer driver');
  }
}
```

### Modificación en Backend (complete-payment)

El endpoint `POST /api/payments/pos/complete-payment` ahora retorna `receipt_id` para que el frontend pueda imprimir:

```json
{
  "success": true,
  "order_id": "uuid",
  "order_number": "ORD-20260424-ABC12",
  "receipt": { ... },
  "receipt_id": "uuid-del-receipt"
}
```

### Consideraciones de Rendimiento

1. **HTML Preview:** Se abre en nueva pestaña - no bloquea la UI
2. **Print silencioso:** No muestra confirmación visual (solo logs)
3. **ESCPOS:** La operación puede tardar 1-2 segundos

### Checklist de Implementación Frontend

- [x] Funciones de API agregadas a `api.js`
- [x] Panel de configuración colapsable en Cashier
- [x] Detección de driver al confirmar pago
- [x] Acción condicional según tipo de driver
- [x] Botón para cambiar driver con feedback visual
- [x] Endpoint `complete-payment` retorna `receipt_id`