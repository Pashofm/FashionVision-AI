# Integración Terminal POS (Punto de Venta)

## Resumen

Este documento describe la integración del sistema FashionVision AI con terminales de punto de venta (POS) para procesamiento de pagos con tarjeta.

## Opciones de Integración Consideradas

### 1. Stripe Terminal
**Pros:**
- API bien documentada
- Soporte para lectores de tarjetas físicos (Stripe Reader S124)
- Integración con el ecosistema Stripe (mismas credenciales que el procesamiento de pagos online)
- Sandbox de pruebas robusto
- Soporte para múltiples idiomas y monedas

**Cons:**
- Requiere cuenta Stripe Business
- Costos de transacción (2.9% + $0.30 USD por transacción)
- Necesita hardware específico para uso real
- Solo funciona con tarjetas (no efectivo)

### 2. Square Terminal
**Pros:**
- Hardware dedicado (Square Terminal)
- Sin mensualidades, solo costo por transacción
- Dashboard unificado para inventario y ventas

**Cons:**
- Disponible principalmente en EE.UU. y Reino Unido
- Menos flexible para integraciones personalizadas

### 3. Adyen Terminal API
**Pros:**
- Soporte global
- Terminales de múltiples fabricantes (Ingenico, Verifone, etc.)
- Una sola API para múltiples métodos de pago

**Cons:**
- Requiere contrato comercial con Adyen
- Proceso de onboarding complejo
- Costos variables según volumen

### 4. Mock Terminal (Implementación Actual)
**Pros:**
- No requiere hardware ni cuentas externas
- Perfecto para desarrollo y pruebas
- Simula el flujo completo de una transacción

**Cons:**
- No procesa pagos reales
- Solo para testing

## Decisión Actual

Se implementó un **Mock Terminal** que simula el flujo de un terminal POS real. Esto permite:

1. **Desarrollo sin hardware** - Los desarrolladores pueden probar el flujo completo
2. **Testing automatizado** - Scripts para simular diferentes escenarios
3. **Prototipo funcional** - La interfaz de usuario está lista para conectar con un terminal real

## Implementación Mock

### Estructura del Proyecto

```
backend/
├── app/
│   └── services/
│       └── pos_terminal.py      # Mock POS Terminal
├── scripts/
│   └── test_pos_terminal.py    # Script de pruebas
```

### Flujo de Transacción Mock

```
1. initialize_payment(amount)
   └── Retorna: {transaction_id, status: "waiting_card"}

2. wait_for_card_present(transaction_id)
   └── Retorna: {success: true/false, status: "processing"/"timeout"}

3. process_payment(transaction_id)
   └── Simula procesamiento (1.5 segundos)
   └── Retorna: {status: "approved"/"declined"/"timeout", auth_code, etc.}

4. cancel_transaction(transaction_id)
   └── Cancela la transacción en curso
```

### Configuración de Probabilidades

| Resultado | Probabilidad |
|-----------|--------------|
| Aprobado  | 70%          |
| Rechazado | 20%          |
| Timeout   | 10%          |

Para cambiar estas probabilidades:

```python
from backend.app.services.pos_terminal import terminal

terminal.approval_rate = 0.80  # 80% aprobación
terminal.decline_rate = 0.15    # 15% rechazo
terminal.timeout_rate = 0.05    # 5% timeout
```

## Endpoints de la API

### POST /api/payments/pos/init
Inicializa un pago en el terminal.

```json
Request:
{
  "cart_id": "uuid-del-carrito",
  "amount": 599.99,
  "currency": "MXN"
}

Response:
{
  "success": true,
  "transaction_id": "TXN-ABC123DEF456",
  "status": "waiting_card",
  "amount": 599.99
}
```

### POST /api/payments/pos/wait-card
Espera a que se presente la tarjeta.

```json
Response:
{
  "success": true,
  "transaction_id": "TXN-ABC123DEF456",
  "status": "processing"
}
```

### POST /api/payments/pos/process
Procesa el pago (puede tomar 1-2 segundos).

```json
Response:
{
  "success": true,
  "transaction_id": "TXN-ABC123DEF456",
  "status": "approved",
  "amount": 599.99,
  "card_last_four": "4242",
  "authorization_code": "AUTH-123456",
  "provider_reference": "REF-A1B2C3D4"
}
```

### POST /api/payments/pos/cancel
Cancela una transacción activa.

```json
Response:
{
  "success": true,
  "transaction_id": "TXN-ABC123DEF456",
  "status": "cancelled"
}
```

### GET /api/payments/pos/status/{transaction_id}
Obtiene el estado actual de una transacción.

### GET /api/payments/pos/result/{transaction_id}
Obtiene el resultado completo de una transacción completada.

### POST /api/payments/pos/complete-payment
Completa el pago en el sistema (despues de que el terminal aprueba).

```json
Request:
{
  "transaction_id": "TXN-ABC123DEF456",
  "cart_id": "uuid-del-carrito"
}

Response:
{
  "success": true,
  "order_id": "uuid-de-la-orden",
  "order_number": "ORD-20240115-00001",
  "receipt": {
    "receipt_number": "REC-20240115-00001",
    "items": [...],
    "subtotal": 517.23,
    "tax_amount": 82.76,
    "total_amount": 599.99,
    "payment_method": "card",
    "card_last_four": "4242",
    "authorization_code": "AUTH-123456"
  }
}
```

## Scripts de Testing

### Ejecutar Tests del Terminal POS

```bash
cd backend
source venv/bin/activate
python scripts/test_pos_terminal.py
```

### Escenarios de Prueba

1. **Transacción Aprobada** - Simula pago exitoso
2. **Transacción Rechazada** - Simula rechazo del banco
3. **Timeout** - Simula tarjeta no detectada
4. **Cancelación** - Simula cancelación por el usuario
5. **Múltiples Transacciones** - Estadísticas de distribución

## Cambios para Producción

### Para usar Stripe Terminal:

1. **Crear cuenta Stripe Business**
   - Ir a https://dashboard.stripe.com/register
   - Completar verificación KYC

2. **Obtener credenciales API**
   - Stripe Publishable Key
   - Stripe Secret Key
   - Stripe Webhook Secret

3. **Adquirir hardware**
   - Stripe Reader S124 (lector de tarjetas)
   - O usar Stripe Terminal SDK para simulators

4. **Instalar SDK**
   ```bash
   pip install stripe
   ```

5. **Implementar en `pos_terminal.py`**

```python
import stripe
stripe.api_key = "sk_live_..."

class StripePOS:
    def __init__(self):
        self.terminal = stripe.terminal.ConnectionToken.create()

    async def initialize_payment(self, amount, currency="MXN"):
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe usa centavos
            currency=currency,
            payment_method_types=["card_present"],
            capture_method="manual"
        )
        return {
            "transaction_id": intent.id,
            "client_secret": intent.client_secret
        }
```

### Consideraciones de Seguridad

1. **PCI DSS** - No almacenar datos de tarjeta
2. **HTTPS** - Todos los endpoints deben usar HTTPS
3. **Webhooks** - Verificar firmas de webhooks
4. **Logs** - No registrar números de tarjeta completos

### Variables de Entorno Necesarias

```env
# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Para testing
STRIPE_TEST_MODE=true
```

## Checklist de Implementación

- [x] Mock terminal service creado
- [x] Endpoints API implementados
- [x] Frontend de Cashier modificado
- [x] Script de testing creado
- [ ] Documentación de API completada
- [ ] Webhook handlers implementados (para producción)
- [ ] Retry logic implementada
- [ ] Manejo de errores mejorado
- [ ] Hardware real probado (cuando esté disponible)