# 04 · Seguridad y Cumplimiento Normativo

> **Nota para IAs y auditores de seguridad:**  
> La seguridad de esta plataforma sigue el estándar OWASP ASVS 5.0 Nivel 2 y las normativas chilenas vigentes (Ley 21.719 de Protección de Datos y Ley 21.663 Marco de Ciberseguridad).

> **Estado:** lo descrito aquí son controles de diseño. El portal aún no está implementado (ver `tasks/plan.md`); cada control se marca como hecho cuando su tarea se completa.

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
