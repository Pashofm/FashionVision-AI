# ADR-003: Arquitectura de Sesión Dual (Auth + Kiosk)

**Estado:** Aceptado  
**Fecha:** 2024  
**Participantes:** Equipo de desarrollo

---

## Contexto

El sistema tiene dos tipos de usuarios con necesidades muy diferentes de sesión:
1. **Admin/Cajero**: Inicia sesión con email y contraseña, necesita una sesión persistente con JWT
2. **Cliente Kiosko**: Usa una estación física en la tienda sin login tradicional, pero necesita un contexto de sesión para su carrito y detecciones

Se necesita una arquitectura de sesiones que maneje ambos casos.

## Opciones Consideradas

### Opción A: Sesión dual (auth + kiosk)
Dos tipos de sesión en el mismo modelo:
- Sesiones auth: vinculadas a un usuario (user_id), requieren login
- Sesiones kiosk: vinculadas a una estación (station_id), se crean automáticamente

### Opción B: Solo sesiones auth
Los clientes del kiosko deben crear una cuenta o usar un usuario genérico. No hay distinción entre tipos de sesión.

### Opción C: Sesiones completamente separadas
Dos tablas y modelos independientes para sesiones auth y sesiones kiosk.

## Decisión

**Seleccionada: Opción A — Sesión dual en modelo unificado**

## Justificación

1. **Reutilización de infraestructura**: Mismo modelo, tabla y endpoints para ambos tipos de sesión
2. **Flexibilidad**: Una sesión kiosk puede opcionalmente vincularse a un usuario autenticado (client_user_id nullable)
3. **Simplicidad**: No requiere lógica duplicada para manejo de timeouts, limpieza, y estado
4. **Timeout diferenciado**: Las sesiones kiosk expiran a los 2 minutos de inactividad (configurable), las sesiones auth expiran según el JWT

## Flujo de Sesión Kiosk

```
Cliente se acerca → POST /sessions (station_id: "kiosk-1") → Sesión activa
→ Cliente escanea prendas → Se extiende sesión en cada interacción
→ 2 min sin actividad → Countdown 10s → Sesión abandonada → Limpieza
```

## Flujo de Sesión Auth

```
Usuario → POST /auth/login → JWT tokens → Sesión vinculada al user_id
→ Peticiones autenticadas con Bearer token
→ Logout → last_logout_at actualizado → Tokens previos invalidados
```

## Consecuencias

- El modelo `Session` tiene `user_id` nullable (null para kiosk, valor para auth)
- `station_id` identifica la estación física del kiosko
- `client_user_id` permite vincular opcionalmente un usuario a una sesión kiosk
- La limpieza de sesiones expiradas es asíncrona (cada 5 minutos)
- La extensión de sesión (`/auth/session/extend`) actualiza `last_activity_at`
