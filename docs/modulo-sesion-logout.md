# Módulo de Sesión y Logout - FashionVision AI

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema de Sesiones](#arquitectura-del-sistema-de-sesiones)
3. [Flujo de Login](#flujo-de-login)
4. [Módulo Cliente (Kiosko)](#módulo-cliente-kiosko)
5. [Módulo Admin y Caja](#módulo-admin-y-caja)
6. [Timeout de Sesión](#timeout-de-sesión)
7. [Invalidación de Tokens](#invalidación-de-tokens)
8. [Endpoints de API](#endpoints-de-api)
9. [Componentes Frontend](#componentes-frontend)
10. [Base de Datos](#base-de-datos)
11. [Estados de Error](#estados-de-error)

---

## Descripción General

Este módulo gestiona el sistema de autenticación, sesiones y logout para tres tipos de usuarios:

| Rol | Comportamiento | Interfaz |
|-----|----------------|----------|
| **Client** | Auto-logout con countdown | Pantalla táctil kiosko |
| **Admin** | Logout manual | Dashboard con botón |
| **Cashier** | Logout manual | Caja con botón |

El módulo cliente está diseñado para usarse en pantallas táctiles en tiendas de ropa donde los clientes interactúan directamente con el sistema.

---

## Arquitectura del Sistema de Sesiones

El sistema maneja dos tipos de sesiones independientes pero relacionadas:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION SESSION                            │
│                    (access_token / refresh_token)                    │
├─────────────────────────────────────────────────────────────────────┤
│  Propósito:          Autenticación para todas las API calls        │
│  Almacenamiento:     localStorage                                   │
│  Duración:           Access token: 15 min / Refresh: 7 días        │
│  Refresh:            Automático cuando expira dentro de 60s        │
│  Invalidate:         Al hacer logout o invalidar refresh token     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         KIOSK SESSION                                │
│                    (client_session_id / cart_id)                    │
├─────────────────────────────────────────────────────────────────────┤
│  Propósito:          Tracking de carrito de compras en kiosko       │
│  Almacenamiento:     localStorage                                   │
│  Duración:           2 min de inactividad → countdown 10 seg        │
│  Extender:           Al interactuar (cámara, carrito, etc.)         │
│  Limpiar:            Al hacer logout o timeout                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Relación entre sesiones

```
                    LOGIN
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   access_token    refresh_token   user object
   (localStorage)  (localStorage)   (localStorage)
        │              │              │
        ▼              ▼              ▼
  Todas las API    Refresh token   Role check
   requests        cuando expire    para rutas

   ┌─────────────────────────────────────────────┐
   │           CLIENT (KIOSK) ONLY               │
   ├─────────────────────────────────────────────┤
   │  client_session_id (localStorage)           │
   │  client_cart_id (localStorage)              │
   └─────────────────────────────────────────────┘
```

---

## Flujo de Login

```
┌──────────────────────────────────────────────────────────────────┐
│                           LOGIN FLOW                             │
└──────────────────────────────────────────────────────────────────┘

   ┌─────────┐    ┌──────────────┐    ┌──────────────────────────┐
   │  User   │───►│  login.jsx   │───►│   POST /api/auth/login   │
   │Entradas │    │  apiLogin()  │    │                          │
   └─────────┘    └──────────────┘    └───────────┬──────────────┘
                                                  │
                              ┌───────────────────┘
                              ▼
                ┌─────────────────────────────┐
                │   Response:                 │
                │   - access_token           │
                │   - refresh_token          │
                │   - user (con role)        │
                └───────────┬─────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      admin             cashier            client
         │                 │                 │
         ▼                 ▼                 ▼
    /dashboard          /caja           /cliente
                                                      │
                                                      ▼
                                            ┌─────────────────────┐
                                            │ initSession()       │
                                            │ - createSession()   │
                                            │ - getOrCreateCart()  │
                                            │ - Store client_*_id  │
                                            └─────────────────────┘
```

### Código: Login (login.jsx)

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  const result = await apiLogin(email, password);
  const role = result.user.role;

  if (role === 'admin') navigate('/dashboard');
  else if (role === 'cashier') navigate('/caja');
  else navigate('/cliente');
};
```

---

## Módulo Cliente (Kiosko)

### Descripción

El módulo cliente es una interfaz de kiosko táctil para tiendas de ropa. Permite a los clientes:
- Abrir cámara y capturar imágenes
- Detectar prendas mediante YOLO
- Agregar productos al carrito
- Enviar pedidos a caja

### Flujo del Timeout

```
┌──────────────────────────────────────────────────────────────────┐
│                      KIOSK TIMEOUT FLOW                          │
└──────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  useKioskTimeout (hook)                                     │
  │                                                             │
  │  INICIO: Timer de 2 minutos (sin importar actividad)       │
  │          │                                                  │
  │          ▼                                                  │
  │  ┌──────────────────────────────────────┐                  │
  │  │  isAuthenticated()?                   │                  │
  │  │  - Verifica access_token existe      │                  │
  │  └──────────────┬───────────────────────┘                  │
  │                 │                                           │
  │          ┌──────▼──────┐                                    │
  │          │ START TIMER │                                    │
  │          │ 2 minutos   │                                    │
  │          └──────┬──────┘                                    │
  │                 │                                           │
  │          ┌──────▼──────┐                                    │
  │          │  TIMER DONE  │────────────┐                       │
  │          └──────┬──────┘            │                       │
  │                 │                   ▼                       │
  │                 │         ┌─────────────────┐               │
  │                 │         │ START COUNTDOWN │               │
  │                 │         │   10 segundos   │               │
  │                 │         └────────┬────────┘               │
  │                 │                  │                         │
  │                 │         ┌────────▼────────┐               │
  │                 │         │ COUNTDOWN === 0 │               │
  │                 │         └────────┬────────┘               │
  │                 │                  │                         │
  │                 │         ┌────────▼────────┐               │
  │                 │         │ performLogout() │               │
  │                 │         │ - POST /logout  │               │
  │                 │         │ - Clear local   │               │
  │                 │         │ - navigate('/')│               │
  │                 │         └─────────────────┘               │
  │                 └──────────────────────────────────────────┘
  └─────────────────────────────────────────────────────────────┘
```

### Extender Sesión (Mantener Sesión)

Cuando el usuario hace click en "Mantener sesión":

```javascript
const resetTimer = useCallback(async () => {
  // 1. Limpia timers existentes
  clearAllTimers();
  setCountdown(null);

  // 2. Avisa al servidor que usuario está activo
  try {
    await extendSession();  // PUT /api/auth/session/extend
  } catch (err) {
    console.warn('Failed to extend session on server:', err);
  }

  // 3. Reinicia timer de 2 minutos
  startKioskTimer();
}, [...]);
```

### Actividades que Extienden la Sesión

En el módulo cliente, las siguientes operaciones llaman a `extendSession()`:

| Operación | Función | Descripción |
|-----------|---------|-------------|
| Abrir cámara | `openCamera()` | Usuario toca "Abrir Cámara" |
| Capturar imagen | `handleCapture()` | Usuario captura una foto |
| Agregar al carrito | `agregarAlCarrito()` | Producto añadido |
| Eliminar del carrito | `eliminarDelCarrito()` | Producto eliminado |

### Countdown UI

Cuando el timer expira, se muestra un overlay fullscreen con el countdown:

```jsx
{showCountdown && countdown !== null && (
  <div className="countdown-overlay">
    <div className="countdown-modal">
      <h2 className="countdown-title">Tu sesión está por terminar</h2>
      <p className="countdown-subtitle">¿Deseas continuar?</p>
      <div className="countdown-number">{countdown}</div>
      <p className="countdown-text">segundos</p>
      <button className="btn-keep-session" onClick={resetTimer}>
        Mantener sesión
      </button>
    </div>
  </div>
)}
```

### Estilos CSS (countdown-overlay)

```css
.countdown-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.countdown-modal {
  background: white;
  border-radius: 24px;
  padding: 48px;
  text-align: center;
  max-width: 400px;
}

.countdown-number {
  font-size: 96px;
  font-weight: bold;
  color: #764ba2;
  line-height: 1;
}
```

---

## Módulo Admin y Caja

### Logout Manual

Admin y Caja tienen un botón "Cerrar sesión" en el header de su interfaz.

```
┌──────────────────────────────────────────────────────────────────┐
│                     LOGOUT FLOW (Admin/Caja)                     │
└──────────────────────────────────────────────────────────────────┘

   ┌────────────┐    ┌─────────────────┐    ┌──────────────────────┐
   │  Click     │───►│ handleLogout()  │───►│ performLogout()      │
   │"Cerrar     │    │                 │    │                      │
   │ sesión"    │    │                 │    │ 1. POST /api/auth/    │
   └────────────┘    │                 │    │      logout          │
                     │                 │    │                      │
                     │                 │    │ 2. logout()          │
                     │                 │    │    - clear localStorage│
                     └────────┬────────┘    └────────┬─────────────┘
                              │                      │
                              │         ┌────────────▼────────────┐
                              └────────►│      navigate('/')       │
                                        └───────────────────────────┘
```

---

## Timeout de Sesión

### Configuración

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `KIOSK_TIMEOUT_MS` | 120,000 ms (2 min) | Tiempo antes de mostrar countdown |
| `COUNTDOWN_SECONDS` | 10 | Segundos de countdown antes de logout |
| `TOKEN_REFRESH_BUFFER_SECONDS` | 60 | Cuándo empezar a refrescar token |

### Timer del Kiosko (useKioskTimeout.js)

```javascript
const KIOSK_TIMEOUT_MS = 2 * 60 * 1000;  // 2 minutos
const COUNTDOWN_SECONDS = 10;

export function useKioskTimeout(onSessionEnd) {
  const timeoutRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  const sessionEndingRef = useRef(false);
  const [countdown, setCountdown] = useState(null);

  // El timer corre SIN importar actividad del usuario
  useEffect(() => {
    if (isAuthenticated()) {
      startKioskTimer();
    }
    return () => clearAllTimers();
  }, [startKioskTimer, clearAllTimers]);

  // Cuando countdown llega a 0, se llama onSessionEnd
  useEffect(() => {
    if (sessionEndingRef.current && countdown === null) {
      sessionEndingRef.current = false;
      if (onSessionEnd) onSessionEnd();
    }
  }, [countdown, onSessionEnd]);

  return { countdown, resetTimer };
}
```

---

## Invalidación de Tokens

### Mecanismo

El sistema utiliza `last_logout_at` en la tabla `users` para invalidar tokens antiguos:

```
┌──────────────────────────────────────────────────────────────────┐
│                 TOKEN INVALIDATION FLOW                           │
└──────────────────────────────────────────────────────────────────┘

  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐
  │ User hace    │───►│ POST /api/auth/ │───►│ last_logout_at =  │
  │ logout       │    │ logout          │    │ NOW (UTC)         │
  └──────────────┘    └─────────────────┘    └───────────────────┘

  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐
  │ Token viejo  │───►│ POST /api/auth/ │───►│ Decode payload    │
  │ intenta      │    │ refresh         │    │ Obtener iat       │
  │ refresh      │    │                 │    │                   │
  └──────────────┘    └─────────────────┘    └───────┬───────────┘
                                                      │
                                     ┌────────────────┴───────────┐
                                     ▼                             ▼
                         ┌─────────────────┐           ┌─────────────────┐
                         │  iat >          │           │  iat <          │
                         │  last_logout_at │           │  last_logout_at │
                         │  → CONTINUE     │           │  → REJECT       │
                         └─────────────────┘           └─────────────────┘
```

### Implementación en Auth Service

```python
def create_refresh_token(user_id: str) -> str:
    data = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.utcnow().isoformat()  # Issued at
    }
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_token_issued_at(payload: dict) -> Optional[datetime]:
    iat_str = payload.get("iat")
    if iat_str:
        try:
            return datetime.fromisoformat(iat_str)
        except ValueError:
            pass
    return None
```

### Validación en Refresh

```python
@app.post("/api/auth/refresh")
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession):
    payload = decode_refresh_token(request.refresh_token)
    # ... validación básica ...

    user = result.scalar_one_or_none()

    # VALIDACIÓN CLAVE: Si el usuario hizo logout después de que
    # este token fue creado, se rechaza el refresh
    if user.last_logout_at:
        token_iat = get_token_issued_at(payload)
        if token_iat and token_iat.replace(tzinfo=dt_timezone.utc) < user.last_logout_at:
            raise HTTPException(
                status_code=401,
                detail="Session has been invalidated. Please login again.",
            )

    # Generar nuevos tokens
    access_token = create_access_token(...)
    new_refresh_token = create_refresh_token(...)
```

---

## Endpoints de API

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login con email/password |
| POST | `/api/auth/refresh` | Refrescar access token |
| POST | `/api/auth/logout` | Invalidar sesión del usuario |
| GET | `/api/auth/session/extend` | Extender sesión del servidor |
| PUT | `/api/auth/session/timeout` | Configurar timeout (admin) |
| GET | `/api/auth/session/status` | Estado de la sesión |

### Detalle de Endpoints

#### POST /api/auth/logout

```python
@app.post("/api/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    user_id = current_user.id
    result = await db.execute(
        update(User).where(User.id == user_id).values(
            last_logout_at=datetime.now(dt_timezone.utc)
        )
    )
    await db.commit()
    return {"status": "logged_out", "user_id": str(user_id)}
```

**Request:** Header con Bearer token
**Response:** `{"status": "logged_out", "user_id": "..."}`

#### GET /api/auth/session/extend

```python
@app.get("/api/auth/session/extend")
async def extend_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    session_id_param = None
    try:
        session_id_param = uuid.UUID(current_user.id)
    except Exception:
        pass

    if session_id_param:
        await SessionManager.extend_session(db, session_id_param)

    return {
        "status": "extended",
        "timeout_minutes": SessionManager.get_timeout_minutes()
    }
```

**Request:** Header con Bearer token
**Response:** `{"status": "extended", "timeout_minutes": 30}`

---

## Componentes Frontend

### Estructura de Archivos

```
frontend/src/
├── hooks/
│   └── useKioskTimeout.js       # Timer y countdown para kiosko
├── pages/
│   ├── ClientDetection.jsx      # Interfaz kiosko cliente
│   ├── Dashboard.jsx            # Admin dashboard
│   ├── Cashier.jsx              # Interfaz caja
│   └── login.jsx                # Página de login
├── services/
│   └── api.js                   # Funciones de API
└── styles/
    ├── client-detection.css     # Estilos kiosko
    ├── home.css                 # Estilos caja
    └── Dashboard.css            # Estilos admin
```

### Hook: useKioskTimeout

**Ubicación:** `frontend/src/hooks/useKioskTimeout.js`

**Props:**
- `onSessionEnd`: Callback llamado cuando el countdown llega a 0

**Returns:**
- `countdown`: Número actual del countdown (null si no está activo)
- `resetTimer`: Función para reiniciar el timer

**Uso:**
```javascript
const { countdown, resetTimer } = useKioskTimeout(handleKioskLogout);
```

### ClienteDetection

**Ubicación:** `frontend/src/pages/ClientDetection.jsx`

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| `initSession()` | Crea o recupera sesión de kiosko y carrito |
| `handleKioskLogout()` | Logout completo del kiosko |
| `agregarAlCarrito()` | Añade producto y extiende sesión |
| `eliminarDelCarrito()` | Elimina producto y extiende sesión |
| `handleCapture()` | Captura imagen y extiende sesión |
| `enviarAlAdmin()` | Envía carrito a caja |

### api.js - Funciones de Auth

```javascript
// Verifica si hay token
export function isAuthenticated() {
  return !!localStorage.getItem('access_token');
}

// Limpia localStorage (solo cliente local)
export function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('expires_in');
  localStorage.removeItem('user');
}

// Logout con invalidación server-side
export async function performLogout() {
  try {
    await authenticatedFetch(`${API_URL}/api/auth/logout`, { method: 'POST' });
  } catch (err) {
    console.warn('Server logout failed, clearing local state anyway:', err);
  }
  logout();
}

// Extender sesión en servidor
export async function extendSession() {
  const response = await authenticatedFetch(`${API_URL}/api/auth/session/extend`);
  return response.json();
}
```

---

## Base de Datos

### Modelo User (modificado)

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_logout_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True  # NUEVO CAMPO
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### Campo last_logout_at

- **Tipo:** `DateTime(timezone=True)` o `NULL`
- **Propósito:** Almacenar cuándo el usuario hizo logout por última vez
- **Uso:** Invalidar tokens creados antes de este momento
- **Actualización:** En `POST /api/auth/logout`

---

## Estados de Error

### Errores de Auth

| Código | Mensaje | Causa |
|--------|---------|-------|
| 401 | "Invalid or expired refresh token" | Refresh token malformado o expirado |
| 401 | "User not found or inactive" | Usuario no existe o está desactivado |
| 401 | "Session has been invalidated" | Usuario hizo logout después de crear el token |
| 401 | "Invalid or expired token" | Access token inválido |
| 403 | "Access denied" | Rol insuficiente para el endpoint |

### Errores del Cliente

| Código | Mensaje | Causa |
|--------|---------|-------|
| - | "Error al inicializar el sistema" | Fallo en initSession() |
| - | "No se detectó una prenda" | YOLO no encontró prendas |
| - | "Error al procesar la imagen" | Fallo en detectClothes() |
| - | "Error al agregar al carrito" | Fallo en addCartItem() |

---

## Flujo Completo de Sesión Cliente

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    SESIÓN CLIENTE COMPLETA                                  │
└────────────────────────────────────────────────────────────────────────────┘

1. LOGIN
   Login → access_token/refresh_token en localStorage → navigate('/cliente')

2. INIT SESSION
   /cliente → initSession()
   ├─► Lee client_session_id y client_cart_id de localStorage
   ├─► Si existen: getCart() para recuperar carrito
   │   └─► Si status == 'building': reutiliza sesión
   │   └─► Si no: crea nueva sesión
   └─► Si no existen: createSession() + getOrCreateCartBySession()

3. USO NORMAL (cada interacción extiende el timer)
   ┌─────────────────────────────────────────────────────────────────┐
   │  Abrir Cámara → extendSession()                                 │
   │  Capturar → extendSession()                                      │
   │  Agregar al carrito → extendSession()                            │
   │  Eliminar del carrito → extendSession()                          │
   │  "Mantener sesión" → extendSession() + reinicia timer           │
   └─────────────────────────────────────────────────────────────────┘

4. TIMEOUT (2 minutos sin actividad)
   Timer expira → Countdown 10 segundos
   ├─► Usuario hace click en "Mantener sesión"
   │      └─► resetTimer() → extendSession() + nuevo timer 2 min
   │
   └─► Countdown llega a 0
          └─► handleKioskLogout()
                 ├─► POST /api/auth/logout → last_logout_at = NOW
                 ├─► logout() → limpia localStorage
                 │      - access_token
                 │      - refresh_token
                 │      - expires_in
                 │      - user
                 │      - client_session_id
                 │      - client_cart_id
                 └─► navigate('/') → Login

5. REFRESH DE TOKEN ( Background)
   ├─► authenticatedFetch() detecta token por expirar
   ├─► handleUnauthorized() inicia refresh
   ├─► POST /api/auth/refresh con refresh_token
   │      ├─► Verifica last_logout_at
   │      ├─► Si token.iat < last_logout_at → ERROR "Session invalidated"
   │      └─► Si no → genera nuevos tokens
   └─► Si falla: logout() + navigate('/')

6. LOGOUT MANUAL (desde admin/caja)
   handleLogout() → performLogout()
   ├─► POST /api/auth/logout → last_logout_at = NOW
   ├─► logout() → limpia localStorage
   └─► navigate('/')
```

---

## Notas de Implementación

### Por qué no se usa SessionContext

El `SessionContext` original (ahora eliminado) tenía un `useSessionTimeout` que:
- Corría cada 5 minutos
- llamaba `extendSession()` automáticamente

Esto conflictuaba con el `useKioskTimeout` porque:
- Ambos manejaban timeouts diferentes
- El SessionContext se ejecutaba para TODOS los roles, no solo clientes

**Solución:** Eliminar SessionContext y useSessionTimeout, dejando que cada módulo maneje sus propios timeouts.

### Diferencia entre extendSession() y performLogout()

| Función | Propósito | Endpoint |
|---------|-----------|----------|
| `extendSession()` | Solo actualiza `last_activity_at` en servidor | `GET /api/auth/session/extend` |
| `performLogout()` | Invalida tokens Y limpia estado local | `POST /api/auth/logout` + `logout()` |

### Activity Sync

El servidor tiene `SessionManager.update_activity()` pero:
- NO se usa directamente desde el frontend
- Se llama a través de `PUT /api/auth/session/extend`
- El `periodic_session_cleanup` del backend expira sesiones inactivas cada 5 min

---

## Glosario

| Término | Descripción |
|---------|-------------|
| **Kiosko** | Interfaz táctil para clientes en tienda de ropa |
| **Countdown** | Contador regresivo de 10 segundos antes del logout |
| **refresh_token** | Token JWT para obtener nuevos access tokens |
| **last_logout_at** | Timestamp del último logout del usuario |
| **iat** | "Issued at" - timestamp de creación del token |
| **extendSession** | Actualizar actividad de sesión en servidor |
| **performLogout** | Logout completo (server + local) |

---

*Documentación generada: Abril 2026*
*Versión: 1.0*
*Sistema: FashionVision AI - Módulo de Sesión y Logout*