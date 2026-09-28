# 04 · Seguridad y Cumplimiento Normativo

> **Nota para IAs y auditores de seguridad:**  
> La seguridad de esta plataforma sigue el estándar OWASP ASVS 5.0 Nivel 2 y las normativas chilenas vigentes (Ley 21.719 de Protección de Datos y Ley 21.663 Marco de Ciberseguridad).

> **Estado (25-09-2026):** el portal está implementado en local y listo para App Platform; falta el despliegue (tarea 16). La sección 5 marca los controles hechos con su evidencia y la sección 6 lista las alertas pendientes de decisión del usuario. El timeout por inactividad de 30 minutos, el honeypot y Turnstile no están implementados en el portal.

---

## 1. Protección de Datos Personales (Ley 21.719)
- **Formularios de CV y Trabaja con Nosotros:** Los CVs contienen datos sensibles. El formulario requiere un checkbox obligatorio de consentimiento explícito.
- **Plazo de Retención:** Los antecedentes curriculares se retienen por un máximo de **12 meses**, automatizando su borrado periódico.
- **Canal ARCO:** Se dispone de la casilla formal `privacidad@bkb.cl` para atender solicitudes de acceso, rectificación, cancelación u oposición dentro de los plazos legales.

---

## 2. Seguridad en la Aplicación Web (ASVS Nivel 2)
1. **Hashing de Contraseñas:** Argon2id prioritario con parámetros de memoria y tiempo robustos, más verificación contra contraseñas vulneradas.
2. **Control de Sesiones:**
   - Cookies `__Host-`, `HttpOnly`, `Secure` y `SameSite=Lax/Strict`.
   - Timeout por inactividad: 30 minutos (planificado; la v1 del portal solo aplica el máximo absoluto de 12 horas).
   - Duración absoluta máxima de sesión: 12 horas (no hay "recordar sesión" infinito).
3. **Cabeceras de Seguridad (HTTP Headers):**
   - `Content-Security-Policy`: Sin `unsafe-inline` innecesario.
   - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`.
   - `X-Frame-Options: DENY` para prevenir clickjacking.
   - `X-Content-Type-Options: nosniff`.
4. **Protección Anti-Automatización (Bots):**
   - Campos honeypot trampa en formularios de contacto.
   - Integración prevista con Cloudflare Turnstile sin cookies de rastreo comercial.
   - Límite de intentos con `django-axes` para mitigar ataques de fuerza bruta.

---

## 3. Seguridad en la Infraestructura
- **Aislamiento por Subdominios:** El sitio estático (`www.empresabkb.cl`) y el portal transaccional (`portal.empresabkb.cl`) no comparten cookies ni estado.
- **Base de Datos Privada:** PostgreSQL no cuenta con IP pública; solo acepta conexiones autorizadas provenientes de los servidores de la aplicación en la VPC de DigitalOcean.
- **Secretos:** Gestionados como variables de entorno cifradas en DigitalOcean App Platform, nunca comprometidas en el repositorio Git.

---

## 4. Archivos del Portal (subida y descarga)
Detalle completo en [`03-portal-django.md`](03-portal-django.md).
- **Space privado:** ningún objeto es público. El portal solo escribe bajo el prefijo `portal/` y **nunca** lista, mueve ni borra los archivos antiguos.
- **Acceso por proyecto:** una sola función (`permisos.py`) decide todo. El personal ve todos los proyectos; el cliente solo los que se le asignan, y solo puede ver y descargar. Un proyecto no asignado no existe para el cliente: se responde 404, no 403. Un cliente que intenta subir recibe 403.
- **Descarga:** URL prefirmada de 60 segundos, siempre como adjunto, con registro de usuario, archivo, fecha e IP.
- **Subida:** solo el personal. POST prefirmado con límite de tamaño impuesto por el Space. Lista de extensiones permitidas (sin `zip` ni ejecutables) y máximo de 50 MB. El servidor Django nunca procesa el contenido de los archivos.
- **Sin antivirus en la v1:** solo el personal de BKB sube archivos, no el público. Se sirven siempre como adjunto y solo con extensiones de una lista permitida. ClamAV queda como mejora opcional.
- **Claves del Space:** una clave dedicada al portal, guardada solo en variables de entorno de App Platform y en el `.env` local (nunca versionado).
- **Borrado:** el personal borra lo que él subió y el administrador cualquier archivo; el cliente nunca. Es lógico: oculta el archivo al instante para todos, registra quién lo hizo y el objeto permanece en el Space.

---

## 5. Controles implementados en el portal (25-09-2026)

Cada control cita el setting, el archivo o la prueba que lo demuestra (rutas relativas a `apps/portal/`).

| Hecho | Control | Evidencia |
|---|---|---|
| [x] | Argon2id como hasher principal | `config/settings.py` (`PASSWORD_HASHERS`) |
| [x] | Validadores de contraseña, mínimo 12 caracteres | `config/settings.py` (`AUTH_PASSWORD_VALIDATORS`); `gestion/tests.py::CrearContrasenaTests.test_contrasena_corta_o_comun_se_rechaza` |
| [x] | Bloqueo tras 5 intentos fallidos (django-axes) y error genérico | `AXES_FAILURE_LIMIT = 5`; `accounts/tests/test_login.py` (`test_bloqueo_fuerza_bruta`, `test_error_generico`) |
| [x] | CSP con nonce, sin `unsafe-inline`, sin estilos ni manejadores en línea | `CONTENT_SECURITY_POLICY` en `config/settings.py`; `documentos/tests/test_csp_contrato.py` |
| [x] | Cookies `HttpOnly` y `SameSite` (sesión `Lax`, CSRF `Strict`); con `DEBUG=False`, prefijo `__Host-` y `Secure` | `config/settings.py` |
| [x] | Sesión de 12 horas como máximo absoluto | `SESSION_COOKIE_AGE = 43200` |
| [x] | HSTS (1 año, subdominios, preload), redirección a HTTPS y `SECURE_PROXY_SSL_HEADER` | `config/settings.py` (bloque `if not DEBUG`); `check --deploy` sin advertencias con variables ficticias (tarea 15) |
| [x] | `X-Frame-Options: DENY` | `X_FRAME_OPTIONS` en `config/settings.py` |
| [x] | `SECRET_KEY` obligatoria con `DEBUG=False` | `config/settings.py` (`ImproperlyConfigured`) |
| [x] | Prefijo del Space validado al arrancar | `config/settings.py` (`SPACES_PREFIX`); `documentos/tests/test_storage.py` |
| [x] | Descarga con URL prefirmada de 60 s y como adjunto | `documentos/storage.py`; `test_storage.py` |
| [x] | Subida con POST prefirmado y `content-length-range` | `documentos/storage.py`; `test_storage.py::test_incluye_content_length_range_con_el_maximo_configurado` |
| [x] | El portal no lista ni borra objetos del Space | `test_storage.py::test_no_hay_funciones_para_listar_ni_borrar` |
| [x] | Borrado lógico con registro de quién lo hizo | `Archivo.eliminado_en`/`eliminado_por`; `documentos/tests/test_borrar.py` |
| [x] | Registro de cada descarga con la IP | `DescargaLog`; `test_descarga.py::test_descarga_registra_log_y_redirige` |
| [x] | Permisos centralizados en `permisos.py` y 404 uniforme para lo ajeno | `documentos/permisos.py`; `test_permisos.py`, `test_errores.py::test_404_no_distingue_proyecto_ajeno_de_inexistente` |
| [x] | Enlaces de contraseña de un solo uso, válidos 3 días | `PASSWORD_RESET_TIMEOUT`; `gestion/tests.py`, `accounts/tests/test_contrasena.py` |
| [x] | "¿Olvidaste tu contraseña?" responde igual exista o no el correo, con límite por IP | `accounts/tests/test_contrasena.py` (`test_misma_respuesta_exista_o_no_el_correo`, `LimitePorIpTests`) |
| [x] | El jefe nunca ve ni escribe contraseñas | `gestion/forms.py` (solo nombre, correo y tipo) |
| [ ] | Timeout por inactividad de 30 minutos | No implementado (planificado, ver sección 2) |

## 6. Alertas pendientes de decisión del usuario (antes de la tarea 16)

| Alerta | Riesgo | Propuesta |
|---|---|---|
| axes detrás del proxy de App Platform | axes usa `REMOTE_ADDR`, que en producción es la IP del proxy: 5 logins fallidos de cualquiera bloquearían a todos | Configurar la IP real del cliente para axes y alinear `_get_client_ip` con la misma regla. Bloquea la tarea 16 |
| Arranque sin `EMAIL_HOST` con `DEBUG=False` | Cae al backend de consola: los enlaces de invitación y recuperación quedarían en los logs de App Platform | Que el arranque falle, igual que sin `SECRET_KEY`. Bloquea la tarea 16 |
| Chequeo de salud de App Platform | Si llega por HTTP interno o con un `Host` fuera de `ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT` respondería 301 o Django 400, y el servicio quedaría "no saludable" | Verificar en la tarea 16; si falla, eximir `health/` de la redirección o agregar el host interno (toca seguridad: requiere al usuario) |
